"""
Client connection, background receiver, and terminal interaction.
"""
import json
import socket
import threading
import time
from collections import deque
from config import DEFAULT_PORT, MAX_PLAYERS, paint, clear_screen, flush_stdin
from games import GET_GAME_MODULE
from protocol import decode_message, encode_message
from utils.validation import clean_name


class ClientSession:
    def __init__(self, sock, name):
        self.sock = sock
        self.name = name
        self.send_lock = threading.Lock()
        self.screen_lock = threading.RLock()
        self.turn_event = threading.Event()
        self.over = threading.Event()

        self.my_id = None
        self.game_module = None
        self.view = None
        self.players = []
        self.turn_id = None
        self.turn_name = ""
        self.lobby_players = []
        self.started = False
        self.log = deque(maxlen=6)

    def prompt(self):
        print("  > ", end="", flush=True)

    def say(self, text, error=False):
        with self.screen_lock:
            print(paint(f"  ! {text}", "1;31") if error else f"  {text}")
            if self.turn_event.is_set():
                self.prompt()

    def redraw(self):
        with self.screen_lock:
            clear_screen()
            if not self.started:
                print(paint("=" * 50, "1;36"))
                print(paint("       COLLEGE LAN ARCADE — LOBBY", "1;36"))
                print(paint("=" * 50, "1;36"))
                print(f"\n  Connected as {paint(self.name, '1;33')}")
                print(f"\n  Players ({len(self.lobby_players)}/{MAX_PLAYERS}):")
                for i, p in enumerate(self.lobby_players, 1):
                    p_name = p.get("name", "Guest") if isinstance(p, dict) else str(p)
                    is_host = p.get("host", False) if isinstance(p, dict) else (i == 1)
                    is_ready = p.get("ready", True) if isinstance(p, dict) else True

                    host_tag = " " + paint("[HOST]", "1;33") if is_host else ""
                    you_tag = " " + paint("(you)", "1;36") if p_name == self.name else ""
                    status_tag = " " + paint("[READY]", "1;32") if is_ready else " " + paint("[WAITING]", "31")

                    print(f"    {i}. {p_name:<18}{host_tag}{status_tag}{you_tag}")

                print("\n  Type 'R' to toggle Ready status | Waiting for host to start...")
                return

            if self.game_module and self.view:
                v = dict(self.view)
                v["log"] = list(self.log)
                print(self.game_module.render_dashboard(v))

            if self.turn_id == self.my_id and self.turn_event.is_set():
                prompt_str = self.game_module.prompt_for(self.view, self.my_id) if self.game_module else "Enter action"
                print(paint(f"\n  ▶ YOUR TURN — {prompt_str} (or '! <msg>' to chat):", "1;36"))
                self.prompt()
            elif self.turn_id is not None:
                who = self.turn_name or "another player"
                print(f"\n  Waiting for {who} to take a turn... (Type '! <msg>' to chat)")

    def show_final(self, message):
        with self.screen_lock:
            clear_screen()
            msg_text = message.get("message", "Game Over")
            winners = message.get("winners", [])
            if self.game_module and self.view:
                print(self.game_module.render_final(self.view, msg_text, winners))
            else:
                print(paint(f"\n  {msg_text}", "1;33"))
            print(paint("\n  Press Enter to return to the main menu...", "1;36"))

    def send(self, payload):
        data = encode_message(payload)
        with self.send_lock:
            self.sock.sendall(data)

    def handle(self, message):
        kind = message.get("type")
        if kind == "reject":
            with self.screen_lock:
                print(paint("Could not join: " + message.get("message", "Rejected"), "1;31"))
            self.over.set()
        elif kind == "joined":
            self.my_id = message.get("player_id")
            self.name = message.get("name", self.name)
            self.lobby_players = [{"name": self.name, "ready": False, "host": False}]
            self.redraw()
        elif kind == "lobby":
            self.lobby_players = message.get("players", message.get("names", []))
            if not self.started:
                self.redraw()
        elif kind == "start":
            self.my_id = message.get("you", self.my_id)
            self.name = message.get("name", self.name)
            game_id = message.get("game_id", "bingo")
            self.game_module = GET_GAME_MODULE(game_id)
            self.view = message.get("view", {})
            self.players = message.get("players", [])
            self.started = True
            self.over.clear()
            self.log.append("Game started!")
            self.redraw()
        elif kind == "rematch":
            self.over.clear()
            self.turn_event.clear()
            if message.get("game_id"):
                self.game_module = GET_GAME_MODULE(message.get("game_id"))
            self.log.append("🔄 Host started a rematch!")
            self.redraw()
        elif kind == "turn":
            if message.get("game_id"):
                self.game_module = GET_GAME_MODULE(message.get("game_id"))
            self.turn_id = message.get("player_id")
            self.turn_name = message.get("player_name", "")
            if message.get("view"):
                self.view = message.get("view")
            if self.turn_id == self.my_id:
                self.turn_event.set()
            else:
                self.turn_event.clear()
            self.redraw()
        elif kind == "action_result":
            if message.get("game_id"):
                self.game_module = GET_GAME_MODULE(message.get("game_id"))
            if message.get("view"):
                self.view = message.get("view")
            caller = message.get("caller", "?")
            events = message.get("events", {})
            if isinstance(events, dict) and "log" in events:
                for entry in events["log"]:
                    self.log.append(entry)
            self.redraw()
        elif kind == "chat":
            entry = message.get("entry", f"💬 {message.get('sender')}: {message.get('text')}")
            self.log.append(entry)
            self.redraw()
        elif kind == "notice":
            self.log.append(message.get("message", ""))
            self.redraw()
        elif kind == "error":
            self.say(message.get("message", "Invalid action"), error=True)
        elif kind == "end":
            self.show_final(message)
            self.over.set()

    def receive_loop(self):
        try:
            reader = self.sock.makefile("r", encoding="utf-8")
            for line in reader:
                message = decode_message(line)
                if message:
                    self.handle(message)
                if self.over.is_set():
                    return
        except OSError:
            pass
        finally:
            if not self.over.is_set():
                with self.screen_lock:
                    print(paint("\n  Lost connection to host.", "1;31"))
                self.over.set()

    def ask_move(self):
        flush_stdin()
        while not self.over.is_set():
            raw = input().strip()
            if self.over.is_set() or not self.turn_event.is_set():
                return

            if raw.startswith("!"):
                msg = raw[1:].strip()
                if msg:
                    try:
                        self.send({"type": "chat", "text": msg})
                    except OSError:
                        return
                continue

            valid, result_or_err = self.game_module.parse_action(self.view, self.my_id, raw)
            if not valid:
                self.say(str(result_or_err), error=True)
                continue

            self.turn_event.clear()
            try:
                self.send({"type": "action", "action": raw})
            except OSError:
                return
            return

    def run(self):
        self.send({"type": "join", "name": self.name})
        thread = threading.Thread(target=self.receive_loop, daemon=True)
        thread.start()
        while not self.over.is_set():
            if self.turn_event.wait(0.2):
                self.ask_move()
        thread.join(timeout=1.0)
        if self.started:
            flush_stdin()
            try:
                input()
            except (KeyboardInterrupt, EOFError):
                pass


def join_lan_game():
    raw = input("Host IP address (or ip:port): ").strip()
    if not raw:
        print("Host IP is required.")
        return
    try:
        if ":" in raw:
            host, port_text = raw.split(":")
            port = int(port_text)
        else:
            host = raw
            port_raw = input(f"Port [{DEFAULT_PORT}]: ").strip()
            port = int(port_raw) if port_raw else DEFAULT_PORT

        name = clean_name(input("Your player name: "), "Guest")
        print(f"Connecting to {host}:{port} ...")
        sock = socket.create_connection((host, port), timeout=10)
        sock.settimeout(None)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except (OSError, ValueError) as exc:
        print(f"Could not connect: {exc}")
        return

    session = ClientSession(sock, name)
    try:
        session.run()
    except KeyboardInterrupt:
        print("\nYou left the game.")
    finally:
        try:
            sock.close()
        except OSError:
            pass
