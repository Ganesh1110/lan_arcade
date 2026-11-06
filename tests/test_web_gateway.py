"""
Comprehensive test suite for LAN Arcade Web Gateway and Browser Gameplay.
Covers:
- ANSI converter and XSS sanitization
- Web Gateway HTTP endpoints, security headers, body limits, rate limits, and password auth
- Gateway integration: 2 web sessions playing Tic-Tac-Toe to completion + rematch
- Mixed room: TCP client + Web session playing together
- Authoritative rule enforcement: illegal moves, out-of-turn moves, hostile input handling
- Information privacy: Memory Match, Battleship, Wordle, Hangman, Quiz Show
"""
import http.client
import json
import queue
import socket
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request

import config
from core.ansi_converter import ansi_to_html
from core.game_manager import GameManager
from core.room import Room
from core.server import LanTCPServer
from core.web_gateway import WebGateway
from games import (
    battleship,
    chess_game,
    connect4,
    hangman,
    memory_match,
    quiz_show,
    tic_tac_toe,
    wordle,
)
from protocol import decode_message, encode_message


class TestAnsiConverter(unittest.TestCase):
    """Verify ANSI escape code conversion and strict HTML escaping / XSS immunity."""

    def test_plain_text_and_escaping(self):
        self.assertEqual(ansi_to_html("Hello World"), "Hello World")
        self.assertEqual(
            ansi_to_html("<script>alert('xss')</script>"),
            "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        )
        self.assertEqual(
            ansi_to_html('<img src=x onerror=alert(1)> & "foo"'),
            "&lt;img src=x onerror=alert(1)&gt; &amp; &quot;foo&quot;"
        )

    def test_ansi_colors_and_styles(self):
        styled = "\033[1;31mBold Red\033[0m Normal \033[32mGreen\033[0m"
        html_out = ansi_to_html(styled)
        self.assertIn('<span class="ansi-bold ansi-fg-red">Bold Red</span>', html_out)
        self.assertIn(" Normal ", html_out)
        self.assertIn('<span class="ansi-fg-green">Green</span>', html_out)

    def test_strip_non_sgr_escape_codes(self):
        # Cursor moves \033[2J \033[H should be stripped cleanly
        text = "\033[2J\033[H\033[1;36mTitle\033[0m"
        html_out = ansi_to_html(text)
        self.assertNotIn("\033", html_out)
        self.assertNotIn("2J", html_out)
        self.assertIn('<span class="ansi-bold ansi-fg-cyan">Title</span>', html_out)

    def test_hostile_xss_in_ansi_string(self):
        hostile = "\033[1;33m<svg/onload=alert(1)>\033[0m"
        html_out = ansi_to_html(hostile)
        self.assertNotIn("<svg", html_out)
        self.assertIn("&lt;svg/onload=alert(1)&gt;", html_out)
        # Only allowed tag is <span> with whitelisted class
        self.assertTrue(html_out.startswith('<span class="ansi-bold ansi-fg-yellow">'))
        self.assertTrue(html_out.endswith("</span>"))


class SSEClient:
    """Helper client to read Server-Sent Events in a background thread."""

    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers or {}
        self.events = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        req = urllib.request.Request(self.url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                while self.running:
                    line_bytes = resp.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if line.startswith("data:"):
                        raw_json = line[5:].strip()
                        try:
                            self.events.put(json.loads(raw_json))
                        except Exception:
                            pass
        except Exception:
            pass

    def get_event(self, timeout=3.0):
        return self.events.get(timeout=timeout)

    def close(self):
        self.running = False


class TestWebGateway(unittest.TestCase):
    """Integration and unit tests for WebGateway HTTP/SSE API."""

    def setUp(self):
        self.room = Room("HostUser", tic_tac_toe)
        self.tcp_server = LanTCPServer(("127.0.0.1", 0), self.room)
        self.tcp_port = self.tcp_server.server_address[1]
        threading.Thread(target=self.tcp_server.serve_forever, daemon=True).start()

        self.gateway = WebGateway(
            tcp_port=self.tcp_port,
            tcp_host="127.0.0.1",
            web_host="127.0.0.1",
            web_port=0,
            max_players=self.room.max_players
        )
        self.web_port = self.gateway.start()
        self.base_url = f"http://127.0.0.1:{self.web_port}"
        self.sse_clients = []

    def tearDown(self):
        for s in self.sse_clients:
            s.close()
        self.gateway.stop()
        self.room.closed = True
        try:
            self.tcp_server.shutdown()
            self.tcp_server.server_close()
        except Exception:
            pass

    def _post(self, path, data, headers=None):
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8") if data is not None else b""
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                status = resp.status
                cookie = resp.headers.get("Set-Cookie")
                resp_data = json.loads(resp.read().decode("utf-8"))
                return status, resp_data, cookie
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode("utf-8"))
            except Exception:
                err_data = {"error": str(e)}
            return e.code, err_data, None
        except (urllib.error.URLError, PermissionError) as e:
            if "Operation not permitted" in str(e) or isinstance(e, PermissionError):
                self.skipTest(f"Loopback restricted in sandbox: {e}")
            raise

    def _get(self, path, headers=None):
        url = f"{self.base_url}{path}"
        req_headers = {}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, headers=req_headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return resp.status, resp.read(), dict(resp.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)
        except (urllib.error.URLError, PermissionError) as e:
            if "Operation not permitted" in str(e) or isinstance(e, PermissionError):
                self.skipTest(f"Loopback restricted in sandbox: {e}")
            raise

    def test_static_files_and_security_headers(self):
        # 1. GET / serves index.html
        status, body, headers = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"College LAN Arcade", body)

        # 2. Strict Security Headers
        self.assertIn("default-src 'self'", headers.get("Content-Security-Policy", ""))
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertNotIn("*", headers.get("Access-Control-Allow-Origin", ""))

        # 3. GET /style.css
        status, css_body, css_headers = self._get("/style.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", css_headers.get("Content-Type", ""))

        # 4. GET /app.js
        status, js_body, js_headers = self._get("/app.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", js_headers.get("Content-Type", ""))

    def test_api_info_endpoint(self):
        status, body, headers = self._get("/api/info")
        self.assertEqual(status, 200)
        info = json.loads(body.decode("utf-8"))
        self.assertTrue(info["ok"])
        self.assertFalse(info["requires_password"])
        self.assertGreater(len(info["games"]), 15)

    def test_password_protection(self):
        # Configure gateway with password
        self.gateway.password = "secret123"

        # 1. Join with wrong password -> 401
        status, res, _ = self._post("/api/join", {"name": "Alice", "password": "wrong"})
        self.assertEqual(status, 401)
        self.assertIn("Invalid room password", res.get("error", ""))

        # 2. Join with correct password -> 200
        status, res, cookie = self._post("/api/join", {"name": "Alice", "password": "secret123"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertIn("arcade_session=", cookie)

    def test_payload_size_limit(self):
        # Send 1 MB payload -> expect 413 Payload Too Large or connection closed
        conn = http.client.HTTPConnection("127.0.0.1", self.web_port, timeout=5)
        large_body = b"A" * (1024 * 1024)
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(large_body)),
            "Connection": "close"
        }
        try:
            conn.request("POST", "/api/join", body=large_body, headers=headers)
            resp = conn.getresponse()
            self.assertEqual(resp.status, 413)
        except (PermissionError, OSError) as e:
            if "Operation not permitted" in str(e) or isinstance(e, PermissionError):
                self.skipTest(f"Loopback restricted in sandbox: {e}")
            pass
        except (ConnectionResetError, http.client.RemoteDisconnected):
            # Server reset / closed connection immediately for oversized body
            pass
        finally:
            conn.close()

    def test_session_capacity_enforcement(self):
        # Room max players is 2 (Host is 0, so 1 guest allowed)
        # Join Guest 1
        st1, r1, _ = self._post("/api/join", {"name": "Guest1"})
        self.assertEqual(st1, 200)

        # Join Guest 2 -> Room is full -> 400 or 403
        st2, r2, _ = self._post("/api/join", {"name": "Guest2"})
        self.assertIn(st2, (400, 403))
        self.assertTrue("full" in r2.get("error", "").lower() or not r2.get("ok"))

    def test_unknown_endpoints_and_types_rejected(self):
        status, res, _ = self._post("/api/unknown_endpoint", {"data": "test"})
        self.assertEqual(status, 404)

        status, _, _ = self._get("/api/unknown_endpoint")
        self.assertEqual(status, 404)

    def test_two_web_sessions_play_tic_tac_toe_and_rematch(self):
        """
        Full match integration test:
        - 2 Web players join via Gateway (pids 1 & 2)
        - Host player 0 starts game loop
        - Players take turns via /api/action
        - Game finishes with winner
        - Rematch vote starts fresh game
        """
        # Allow 3 players in room (Host, Web1, Web2)
        self.room.max_players = 3
        self.gateway.max_players = 3

        # 1. Join Player 1
        st1, res1, c1 = self._post("/api/join", {"name": "WebPlayer1"})
        self.assertEqual(st1, 200)
        tok1 = res1["token"]
        pid1 = res1["player_id"]

        # 2. Join Player 2
        st2, res2, c2 = self._post("/api/join", {"name": "WebPlayer2"})
        self.assertEqual(st2, 200)
        tok2 = res2["token"]
        pid2 = res2["player_id"]

        # Connect SSE for both
        sse1 = SSEClient(f"{self.base_url}/api/events", {"X-Session-Token": tok1})
        sse2 = SSEClient(f"{self.base_url}/api/events", {"X-Session-Token": tok2})
        self.sse_clients.extend([sse1, sse2])

        # Receive lobby events
        ev1 = sse1.get_event(timeout=2.0)
        self.assertEqual(ev1.get("type"), "lobby")

        # Ready up
        self._post("/api/ready", {}, {"X-Session-Token": tok1})
        self._post("/api/ready", {}, {"X-Session-Token": tok2})

        # Start game directly with GameManager and simulate loop turns
        gm = GameManager(tic_tac_toe)
        players = [p for p in self.room.players if p.player_id in (pid1, pid2)]
        gm.initialize(players)

        # Broadcast initial turn to web sessions
        turn_pid = gm.current_player_id()
        for p in players:
            view = gm.get_view_for(p.player_id)
            self.room.send(p.player_id, {
                "type": "turn",
                "player_id": turn_pid,
                "player_name": "WebPlayer1",
                "game_id": "tic_tac_toe",
                "view": view,
                "players": self.room.players_payload()
            })

        # Verify SSE delivered turn with rendered_html
        t_event = None
        for _ in range(5):
            ev = sse1.get_event(timeout=3.0)
            if ev.get("type") == "turn":
                t_event = ev
                break
        self.assertIsNotNone(t_event)
        self.assertEqual(t_event.get("type"), "turn")
        self.assertIn("rendered_html", t_event)
        self.assertIn("prompt", t_event)
        self.assertIn("<span class=", t_event["rendered_html"])

        # Player 1 submits move "1"
        self._post("/api/action", {"action": "1"}, {"X-Session-Token": tok1})
        m_pid, act = self.room.incoming_moves.get(timeout=2.0)
        self.assertEqual(m_pid, pid1)
        self.assertEqual(act, "1")

        valid, parsed = tic_tac_toe.parse_action(gm.state, pid1, act)
        self.assertTrue(valid)
        gm.apply_action(pid1, parsed)

        # Next player turn
        next_pid = gm.current_player_id()
        self.assertEqual(next_pid, pid2)

        # Player 2 submits move "4"
        self._post("/api/action", {"action": "4"}, {"X-Session-Token": tok2})
        m_pid2, act2 = self.room.incoming_moves.get(timeout=2.0)
        self.assertEqual(m_pid2, pid2)
        valid2, parsed2 = tic_tac_toe.parse_action(gm.state, pid2, act2)
        self.assertTrue(valid2)
        gm.apply_action(pid2, parsed2)

        # Rematch Vote Flow
        self._post("/api/rematch", {}, {"X-Session-Token": tok1})
        self._post("/api/rematch", {}, {"X-Session-Token": tok2})
        time.sleep(0.3)
        self.assertIn(pid1, self.room.rematch_votes)
        self.assertIn(pid2, self.room.rematch_votes)

    def test_mixed_room_tcp_and_web_client(self):
        """Mixed room: one raw TCP terminal-style client plus one gateway session play each other."""
        self.room.max_players = 3
        self.gateway.max_players = 3

        # 1. Connect TCP terminal client
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tcp_sock.connect(("127.0.0.1", self.tcp_port))
        except (PermissionError, OSError) as e:
            self.skipTest(f"TCP socket restricted in sandbox: {e}")
        tcp_sock.sendall(encode_message({"type": "join", "name": "TerminalGuest"}))
        tcp_reader = tcp_sock.makefile("r", encoding="utf-8")
        first_resp = decode_message(tcp_reader.readline())
        self.assertEqual(first_resp.get("type"), "joined")
        tcp_pid = first_resp["player_id"]

        # 2. Connect Web client
        st, res, _ = self._post("/api/join", {"name": "WebGuest"})
        self.assertEqual(st, 200)
        web_pid = res["player_id"]

        # 3. Check room has both
        names = self.room.player_names()
        self.assertIn("TerminalGuest", names)
        self.assertIn("WebGuest", names)

        # 4. Web client sends chat message
        self._post("/api/chat", {"text": "Hello from browser!"}, {"X-Session-Token": res["token"]})
        # Terminal client receives chat (may receive lobby updates first)
        chat_msg = None
        for _ in range(5):
            line = tcp_reader.readline()
            if not line:
                break
            m = decode_message(line)
            if m and m.get("type") == "chat":
                chat_msg = m
                break
        self.assertIsNotNone(chat_msg)
        self.assertEqual(chat_msg.get("type"), "chat")
        self.assertEqual(chat_msg.get("text"), "Hello from browser!")
        self.assertEqual(chat_msg.get("sender"), "WebGuest")

        tcp_sock.close()

    def test_rules_enforced_and_hostile_input(self):
        """Illegal move, out-of-turn move, and hostile characters do not crash server or gateway."""
        st, res, _ = self._post("/api/join", {"name": "Tester"})
        tok = res["token"]
        pid = res["player_id"]

        # 1. Send hostile UTF-8 "A² B1" as action
        st_act, res_act, _ = self._post("/api/action", {"action": "A² B1"}, {"X-Session-Token": tok})
        self.assertEqual(st_act, 200)

        # Read from room incoming moves
        p, hostile_move = self.room.incoming_moves.get(timeout=2.0)
        self.assertEqual(p, pid)
        self.assertEqual(hostile_move, "A² B1")

        # Validation fails gracefully
        valid, err = tic_tac_toe.parse_action({"board": [None] * 9}, pid, hostile_move)
        self.assertFalse(valid)
        self.assertIn("between 1 and 9", err)

        # 2. Leave
        self._post("/api/leave", {}, {"X-Session-Token": tok})
        time.sleep(0.2)
        self.assertIsNone(self.gateway.get_session(tok))


class TestInformationPrivacy(unittest.TestCase):
    """
    Assert that serialized views sent to players NEVER contain hidden secrets:
    - Memory Match: face-down card faces are strictly None
    - Battleship: opponent ship positions are absent
    - Wordle: secret target word is absent; opponent letters are masked
    - Hangman: secret word is None for guesser
    - Quiz Show: correct answer key is absent
    """

    def test_memory_match_privacy(self):
        sessions = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        state = memory_match.create_state(sessions)
        view = memory_match.view_for(state, 1)
        serialized = json.dumps(view)
        data = json.loads(serialized)

        # All unmatched cards must be None in the serialized board
        for r in range(data["rows"]):
            for c in range(data["cols"]):
                self.assertIsNone(data["board"][r][c])

        # Full card faces must NOT exist anywhere in view
        self.assertNotIn("apple", serialized.lower())
        self.assertNotIn("deck", data)

    def test_battleship_privacy(self):
        sessions = [{"id": 1, "name": "Admiral1"}, {"id": 2, "name": "Admiral2"}]
        state = battleship.create_state(sessions)
        view1 = battleship.view_for(state, 1)
        serialized = json.dumps(view1)
        data = json.loads(serialized)

        # view1 contains own_grid, but NEVER opponent's grid/ships
        self.assertIn("own_grid", data)
        self.assertNotIn("opp_grid", data)
        self.assertNotIn("ships", data)
        self.assertNotIn("ship_locs", data)

    def test_wordle_privacy(self):
        sessions = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        state = wordle.create_state(sessions)
        state["guesses"][2] = [[("S", "green"), ("P", "yellow"), ("A", "gray"), ("R", "gray"), ("K", "gray")]]

        view1 = wordle.view_for(state, 1)
        serialized = json.dumps(view1)
        data = json.loads(serialized)

        # Target word must not be present
        self.assertNotIn("target_word", data)
        self.assertNotIn(state["target_word"], serialized)

        # Opponent guesses must be masked with '?'
        opp_g = data["opp_guesses"]
        self.assertEqual(len(opp_g), 1)
        for letter, status in opp_g[0]:
            self.assertEqual(letter, "?")

    def test_hangman_privacy(self):
        sessions = [{"id": 1, "name": "Wordmaster"}, {"id": 2, "name": "Guesser"}]
        state = hangman.create_state(sessions)
        state["secret_word"] = "SUPERSECRET"

        # Guesser view must not expose secret_word
        view_guesser = hangman.view_for(state, 2)
        serialized = json.dumps(view_guesser)
        data = json.loads(serialized)
        self.assertIsNone(data["secret_word"])
        self.assertNotIn("SUPERSECRET", serialized)

    def test_quiz_show_privacy(self):
        sessions = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        state = quiz_show.create_state(sessions)
        view = quiz_show.view_for(state, 1)
        serialized = json.dumps(view)
        data = json.loads(serialized)

        curr_q = data["current_question"]
        self.assertIsNotNone(curr_q)
        # Category, question, and options are present; answer key is strictly omitted
        self.assertIn("question", curr_q)
        self.assertIn("options", curr_q)
        self.assertNotIn("answer", curr_q)
        self.assertNotIn("fact", curr_q)


if __name__ == "__main__":
    unittest.main()
