"""
Web Gateway Module for LAN Arcade.
Serves static web files, handles HTTP/SSE browser sessions, and relays
messages to the authoritative host TCP server over localhost.
Zero third-party dependencies.
"""
import copy
import html
import http.cookies
import http.server
import json
import os
import queue
import re
import secrets
import socket
import socketserver
import sys
import threading
import time
from typing import Dict, Optional, Tuple

import config
from core.ansi_converter import ansi_to_html
from games import GAMES_REGISTRY, GET_GAME_MODULE
from protocol import decode_message, encode_message
from utils.validation import clean_name

MAX_BODY_SIZE = 65536  # 64 KB limit
IDLE_SESSION_TIMEOUT = 300.0  # 5 minutes
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))

_color_lock = threading.Lock()


class BrowserSession:
    """Represents a connected browser player session backed by a local TCP client socket."""

    def __init__(self, token: str, sock: socket.socket, player_id: int, name: str):
        self.token = token
        self.sock = sock
        self.player_id = player_id
        self.name = name
        self.event_queue: queue.Queue = queue.Queue(maxsize=1000)
        self.last_active = time.time()
        self.last_state: Optional[dict] = None
        self.closed = False
        self.lock = threading.Lock()

    def touch(self):
        self.last_active = time.time()

    def send(self, payload: dict) -> bool:
        if self.closed:
            return False
        data = encode_message(payload)
        with self.lock:
            try:
                self.sock.sendall(data)
                return True
            except OSError:
                self.closed = True
                return False

    def close(self):
        self.closed = True
        try:
            self.sock.close()
        except OSError:
            pass


class WebGatewayServer(http.server.ThreadingHTTPServer):
    """Custom ThreadingHTTPServer holding gateway reference."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, gateway):
        self.gateway = gateway
        super().__init__(server_address, RequestHandlerClass)


class WebRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP and SSE request handler for Web Gateway."""

    server_version = "ArcadeGateway/1.0"

    def log_message(self, format, *args):
        # Silence default stderr logging to keep console clean
        pass

    @property
    def gateway(self):
        return self.server.gateway

    def _send_security_headers(self, content_type: str = "application/json; charset=utf-8"):
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

    def _send_json(self, status_code: int, data: dict, extra_headers: Optional[list] = None):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self._send_security_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if status_code in (413, 500):
            self.send_header("Connection", "close")
            self.close_connection = True
        if extra_headers:
            for k, v in extra_headers:
                self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
            self.wfile.flush()
        except OSError:
            pass

    def _send_error(self, status_code: int, message: str):
        self._send_json(status_code, {"ok": False, "error": message})

    def _get_client_ip(self) -> str:
        peer = self.client_address
        return peer[0] if (isinstance(peer, (tuple, list)) and len(peer) > 0) else "127.0.0.1"

    def _check_rate_limit(self) -> bool:
        ip = self._get_client_ip()
        return self.gateway.check_rate_limit(ip)

    def _get_session_token(self) -> Optional[str]:
        # 1. Cookie header
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            try:
                c = http.cookies.SimpleCookie(cookie_header)
                if "arcade_session" in c:
                    return c["arcade_session"].value
            except Exception:
                pass

        # 2. X-Session-Token header
        token_hdr = self.headers.get("X-Session-Token")
        if token_hdr:
            return token_hdr.strip()

        return None

    def _get_session(self) -> Optional[BrowserSession]:
        token = self._get_session_token()
        if not token:
            return None
        session = self.gateway.get_session(token)
        if session:
            session.touch()
        return session

    def _read_body_json(self) -> Tuple[Optional[dict], Optional[str]]:
        cl_str = self.headers.get("Content-Length")
        if not cl_str:
            return None, "Missing Content-Length header."
        try:
            cl = int(cl_str)
        except ValueError:
            return None, "Invalid Content-Length header."

        if cl < 0:
            return None, "Negative Content-Length."
        if cl > MAX_BODY_SIZE:
            try:
                self.rfile.read(min(cl, MAX_BODY_SIZE))
            except Exception:
                pass
            return None, "Payload too large (exceeds 64 KB)."

        try:
            raw = self.rfile.read(cl)
            if len(raw) != cl:
                return None, "Incomplete body read."
            text = raw.decode("utf-8")
            data = json.loads(text)
            if not isinstance(data, dict):
                return None, "Body must be a JSON object."
            return data, None
        except UnicodeDecodeError:
            return None, "Invalid UTF-8 payload."
        except json.JSONDecodeError:
            return None, "Invalid JSON payload."
        except Exception as e:
            return None, f"Body read error: {e}"

    def do_GET(self):
        try:
            path = self.path.split("?")[0].rstrip("/")
            if not path:
                path = "/"

            if not self._check_rate_limit():
                self._send_error(429, "Too many requests. Please slow down.")
                return

            if path in ("/", "/index.html"):
                self._serve_static_file("index.html", "text/html; charset=utf-8")
            elif path == "/style.css":
                self._serve_static_file("style.css", "text/css; charset=utf-8")
            elif path == "/app.js":
                self._serve_static_file("app.js", "application/javascript; charset=utf-8")
            elif path == "/api/info":
                self._handle_info()
            elif path == "/api/events":
                self._handle_events()
            else:
                self._send_error(404, "Not Found")
        except Exception as e:
            self._send_error(500, f"Server error: {e}")

    def do_POST(self):
        try:
            path = self.path.split("?")[0].rstrip("/")

            if not self._check_rate_limit():
                self._send_error(429, "Too many requests. Please slow down.")
                return

            # Allow-listed POST endpoints
            if path == "/api/join":
                self._handle_join()
            elif path == "/api/action":
                self._handle_action()
            elif path == "/api/ready":
                self._handle_ready()
            elif path == "/api/surrender":
                self._handle_surrender()
            elif path == "/api/chat":
                self._handle_chat()
            elif path == "/api/rematch":
                self._handle_rematch()
            elif path == "/api/leave":
                self._handle_leave()
            elif path == "/api/select_game":
                self._handle_select_game()
            elif path == "/api/start_game":
                self._handle_start_game()
            else:
                self._send_error(404, "Unknown endpoint.")
        except Exception as e:
            self._send_error(500, f"Server error: {e}")

    def _serve_static_file(self, filename: str, content_type: str):
        filepath = os.path.join(WEB_DIR, filename)
        if not os.path.isfile(filepath):
            self._send_error(404, f"File {filename} not found.")
            return

        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self._send_security_headers(content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except OSError as e:
            self._send_error(500, f"Read error: {e}")

    def _handle_info(self):
        games_list = [
            {
                "id": gm.game_id,
                "name": gm.game_name,
                "min": getattr(gm, "min_players", 2),
                "max": getattr(gm, "max_players", 2)
            }
            for gm in GAMES_REGISTRY.values()
        ]
        info = {
            "ok": True,
            "requires_password": bool(self.gateway.password),
            "max_players": self.gateway.max_players,
            "spectator_cap": self.gateway.spectator_cap,
            "games": games_list
        }
        self._send_json(200, info)

    def _handle_join(self):
        cl_str = self.headers.get("Content-Length", "0")
        try:
            if int(cl_str) > MAX_BODY_SIZE:
                self._send_error(413, "Payload too large.")
                return
        except ValueError:
            pass

        data, err = self._read_body_json()
        if err:
            code = 413 if "too large" in err.lower() else 400
            self._send_error(code, err)
            return

        # 1. Password verification
        if self.gateway.password:
            provided_pwd = str(data.get("password", "")).strip()
            if provided_pwd != self.gateway.password:
                self._send_error(401, "Invalid room password.")
                return

        # 2. Session cap enforcement
        active_cnt = self.gateway.session_count()
        allowed_max = self.gateway.max_players + self.gateway.spectator_cap
        if active_cnt >= allowed_max:
            self._send_error(403, f"Room capacity reached ({active_cnt}/{allowed_max} players).")
            return

        # 3. Clean player name
        raw_name = data.get("name", "WebGuest")
        name = clean_name(str(raw_name), "WebGuest")

        # 4. Connect to host TCP port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(5.0)
            sock.connect((self.gateway.tcp_host, self.gateway.tcp_port))
        except OSError as e:
            self._send_error(503, f"Could not connect to host TCP server: {e}")
            return

        # 5. Send join handshake
        try:
            sock.sendall(encode_message({"type": "join", "name": name}))
            reader = sock.makefile("r", encoding="utf-8")
            first_line = reader.readline(65536)
            resp = decode_message(first_line)
            if not resp or resp.get("type") != "joined":
                reason = resp.get("message", "Join rejected by server.") if resp else "Empty response."
                sock.close()
                self._send_error(400, reason)
                return

            player_id = resp["player_id"]
            assigned_name = resp.get("name", name)
        except (OSError, ValueError) as e:
            sock.close()
            self._send_error(500, f"Join exchange failed: {e}")
            return

        # 6. Create BrowserSession
        token = secrets.token_urlsafe(32)
        sock.settimeout(None)
        session = BrowserSession(token, sock, player_id, assigned_name)
        self.gateway.add_session(token, session)

        # 7. Start background TCP reader thread for this session
        t = threading.Thread(target=self.gateway.run_tcp_reader, args=(session,), daemon=True)
        t.start()

        # Set HttpOnly cookie
        cookie = http.cookies.SimpleCookie()
        cookie["arcade_session"] = token
        cookie["arcade_session"]["path"] = "/"
        cookie["arcade_session"]["httponly"] = True
        cookie["arcade_session"]["samesite"] = "Strict"
        cookie_header = cookie.output(header="").strip()

        extra = [
            ("Set-Cookie", cookie_header),
            ("X-Session-Token", token)
        ]
        self._send_json(200, {
            "ok": True,
            "token": token,
            "player_id": player_id,
            "name": assigned_name
        }, extra_headers=extra)

    def _handle_events(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Session not found or expired. Please join again.")
            return

        self.send_response(200)
        self._send_security_headers("text/event-stream; charset=utf-8")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        # Send initial SSE handshake comment
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
        except OSError:
            return

        # Replay latest state if reconnected
        if session.last_state:
            try:
                line = f"data: {json.dumps(session.last_state, ensure_ascii=False)}\n\n"
                self.wfile.write(line.encode("utf-8"))
                self.wfile.flush()
            except OSError:
                return

        # Stream loop
        while not session.closed and self.gateway.running:
            try:
                msg = session.event_queue.get(timeout=15.0)
                line = f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                self.wfile.write(line.encode("utf-8"))
                self.wfile.flush()
            except queue.Empty:
                try:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                except OSError:
                    break
            except (BrokenPipeError, ConnectionResetError, OSError):
                break

    def _handle_action(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Not authenticated.")
            return

        data, err = self._read_body_json()
        if err:
            code = 413 if "too large" in err.lower() else 400
            self._send_error(code, err)
            return

        if "action" not in data:
            self._send_error(400, "Missing 'action' field.")
            return

        action_val = data["action"]
        session.send({"type": "action", "action": action_val})
        self._send_json(200, {"ok": True})

    def _handle_ready(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Not authenticated.")
            return
        session.send({"type": "ready"})
        self._send_json(200, {"ok": True})

    def _handle_surrender(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Not authenticated.")
            return
        session.send({"type": "surrender"})
        self._send_json(200, {"ok": True})

    def _handle_chat(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Not authenticated.")
            return

        data, err = self._read_body_json()
        if err:
            code = 413 if "too large" in err.lower() else 400
            self._send_error(code, err)
            return

        text = str(data.get("text", "")).strip()[:100]
        if text:
            session.send({"type": "chat", "text": text})
        self._send_json(200, {"ok": True})

    def _handle_rematch(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Not authenticated.")
            return
        session.send({"type": "rematch_vote"})
        self._send_json(200, {"ok": True})

    def _handle_leave(self):
        session = self._get_session()
        if session:
            session.send({"type": "leave"})
            self.gateway.remove_session(session.token)
        self._send_json(200, {"ok": True})

    def _handle_select_game(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Not authenticated.")
            return

        data, err = self._read_body_json()
        if err:
            code = 413 if "too large" in err.lower() else 400
            self._send_error(code, err)
            return

        game = str(data.get("game", "")).strip().lower()
        if game in GAMES_REGISTRY:
            session.send({"type": "chat", "text": f"!game {game}"})
            self._send_json(200, {"ok": True})
        else:
            self._send_error(400, f"Unknown game '{game}'.")

    def _handle_start_game(self):
        session = self._get_session()
        if not session:
            self._send_error(401, "Not authenticated.")
            return
        session.send({"type": "chat", "text": "!start"})
        self._send_json(200, {"ok": True})


class WebGateway:
    """Manages the HTTP server, rate limiter, and active browser sessions."""

    def __init__(
        self,
        tcp_port: int,
        tcp_host: str = "127.0.0.1",
        web_host: str = "0.0.0.0",
        web_port: int = 8080,
        password: Optional[str] = None,
        max_players: int = 4,
        spectator_cap: int = 0
    ):
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.web_host = web_host
        self.web_port = web_port
        self.password = password or os.getenv("ARCADE_PASSWORD") or None
        self.max_players = max_players
        self.spectator_cap = spectator_cap

        self.sessions: Dict[str, BrowserSession] = {}
        self.sessions_lock = threading.RLock()

        # Rate limiting: ip -> [tokens, last_refill]
        self.rate_limits: Dict[str, list] = {}
        self.rate_lock = threading.Lock()

        self.running = False
        self.http_server: Optional[WebGatewayServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.bound_port = web_port

    def check_rate_limit(self, ip: str, capacity: float = 40.0, refill_rate: float = 15.0) -> bool:
        now = time.time()
        with self.rate_lock:
            if ip not in self.rate_limits:
                self.rate_limits[ip] = [capacity - 1.0, now]
                return True
            tokens, last = self.rate_limits[ip]
            tokens = min(capacity, tokens + (now - last) * refill_rate)
            if tokens >= 1.0:
                self.rate_limits[ip] = [tokens - 1.0, now]
                return True
            self.rate_limits[ip] = [tokens, now]
            return False

    def add_session(self, token: str, session: BrowserSession):
        with self.sessions_lock:
            self.sessions[token] = session

    def get_session(self, token: str) -> Optional[BrowserSession]:
        with self.sessions_lock:
            return self.sessions.get(token)

    def remove_session(self, token: str):
        with self.sessions_lock:
            sess = self.sessions.pop(token, None)
        if sess:
            sess.close()

    def session_count(self) -> int:
        with self.sessions_lock:
            return len([s for s in self.sessions.values() if not s.closed])

    def run_tcp_reader(self, session: BrowserSession):
        """Background thread reading messages from localhost TCP socket and pushing to SSE queue."""
        try:
            reader = session.sock.makefile("r", encoding="utf-8")
            while self.running and not session.closed:
                line = reader.readline(65536 + 1)
                if not line:
                    break
                if len(line) > 65536:
                    break
                msg = decode_message(line)
                if not msg:
                    continue

                # Augment view payloads with rendered HTML and prompt
                kind = msg.get("type")
                if kind in ("start", "turn", "action_result", "end"):
                    view = msg.get("view")
                    g_id = msg.get("game_id")
                    if view and g_id:
                        gm = GET_GAME_MODULE(g_id)
                        if gm and hasattr(gm, "render_dashboard"):
                            with _color_lock:
                                orig_color = config.USE_COLOR
                                config.USE_COLOR = True
                                try:
                                    dashboard_ansi = gm.render_dashboard(view)
                                finally:
                                    config.USE_COLOR = orig_color
                            msg["rendered_html"] = ansi_to_html(dashboard_ansi)

                        if gm and hasattr(gm, "prompt_for"):
                            try:
                                msg["prompt"] = gm.prompt_for(view, session.player_id)
                            except Exception:
                                msg["prompt"] = "Enter action:"

                        msg["turn_timeout"] = getattr(gm, "turn_timeout", config.TURN_TIMEOUT_SECONDS)

                # Store as last known state for reconnection replay
                if kind in ("lobby", "start", "turn", "action_result", "end"):
                    session.last_state = copy.deepcopy(msg)

                try:
                    session.event_queue.put_nowait(msg)
                except queue.Full:
                    try:
                        session.event_queue.get_nowait()
                        session.event_queue.put_nowait(msg)
                    except Exception:
                        pass
        except (OSError, ValueError):
            pass
        finally:
            session.closed = True
            # Push disconnect notice to browser
            try:
                session.event_queue.put_nowait({
                    "type": "disconnect",
                    "message": "Connection to host closed."
                })
            except Exception:
                pass

    def start(self, port_fallback_range: int = 20) -> int:
        """Start Web Gateway HTTP server in background thread."""
        server = None
        start_port = self.web_port if self.web_port > 0 else 0
        end_port = (self.web_port + port_fallback_range) if self.web_port > 0 else 1
        for try_port in range(start_port, end_port):
            try:
                server = WebGatewayServer((self.web_host, try_port), WebRequestHandler, self)
                self.bound_port = server.server_address[1]
                break
            except OSError:
                continue

        if server is None:
            raise OSError(f"Could not bind web gateway on ports {self.web_port}–{self.web_port + port_fallback_range}.")

        self.http_server = server
        self.running = True

        self.server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        self.server_thread.start()

        # Idle session cleanup timer thread
        threading.Thread(target=self._cleanup_idle_loop, daemon=True).start()
        return self.bound_port

    def _cleanup_idle_loop(self):
        while self.running:
            time.sleep(30.0)
            now = time.time()
            to_remove = []
            with self.sessions_lock:
                for token, s in list(self.sessions.items()):
                    if s.closed or (now - s.last_active > IDLE_SESSION_TIMEOUT):
                        to_remove.append(token)
            for tok in to_remove:
                self.remove_session(tok)

    def stop(self):
        """Shut down the Web Gateway server."""
        self.running = False
        with self.sessions_lock:
            for s in list(self.sessions.values()):
                s.close()
            self.sessions.clear()

        if self.http_server:
            try:
                self.http_server.shutdown()
                self.http_server.server_close()
            except Exception:
                pass
            self.http_server = None
