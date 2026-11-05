"""
Client connection, background receiver, and terminal interaction.
"""
import json
import socket
import threading
import time
from collections import deque
from config import DEFAULT_PORT, MAX_PLAYERS, paint, clear_screen, flush_stdin, play_sound
from games import GET_GAME_MODULE
from protocol import decode_message, encode_message
from utils.discovery import discover_hosts
from utils.input import read_direct_key
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
        self.match_ended = False
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
                print(paint(f"\n  ▶ YOUR TURN — {prompt_str} (or '!ff' to give up, '! <msg>' to chat):", "1;36"))
                self.prompt()
            elif self.turn_id is not None:
                who = self.turn_name or "another player"
                print(f"\n  Waiting for {who} to take a turn... (Type '!ff' to give up, '! <msg>' to chat)")

    def show_final(self, message):
        with self.screen_lock:
            clear_screen()
            msg_text = message.get("message", "Game Over")
            winners = message.get("winners", [])
            if self.game_module and self.view:
                print(self.game_module.render_final(self.view, msg_text, winners))
            else:
                print(paint(f"\n  {msg_text}", "1;33"))
            print(paint("\n  ════════════════════════════════════════════════════════════", "1;36"))
            print(paint("  ⏳ Match Complete! Waiting for host (Rematch / Main Menu)...", "1;33"))
            print(paint("  • If host chooses Rematch, the next round starts automatically!", "2"))
            print(paint("  • Press 'Q' to leave and return to the main menu.", "2"))
            print(paint("  ════════════════════════════════════════════════════════════", "1;36"))

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
            self.match_ended = False
            self.turn_event.clear()
            self.log.clear()
            self.log.append("Game started!")
            self.redraw()
        elif kind == "rematch":
            self.match_ended = False
            self.turn_event.clear()
            if message.get("game_id"):
                self.game_module = GET_GAME_MODULE(message.get("game_id"))
            self.log.clear()
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
                play_sound("turn")
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
            play_sound("chat")
            self.redraw()
        elif kind == "notice":
            self.log.append(message.get("message", ""))
            self.redraw()
        elif kind == "error":
            self.say(message.get("message", "Invalid action"), error=True)
        elif kind == "end":
            msg_text = message.get("message", "")
            if "Host returned to menu" in msg_text or "Not enough players" in msg_text:
                self.match_ended = False
                with self.screen_lock:
                    print(paint(f"\n  ℹ️ {msg_text}", "1;33"))
                    print(paint("  Returning to main menu...", "2"))
                self.over.set()
                return
            play_sound("win")
            self.match_ended = True
            self.turn_event.clear()
            self.show_final(message)
        elif kind == "host_exit":
            self.match_ended = False
            with self.screen_lock:
                print(paint(f"\n  ℹ️ {message.get('message', 'Host returned to main menu.')}", "1;33"))
                print(paint("  Returning to main menu...", "2"))
            self.over.set()

    def receive_loop(self):
        try:
            reader = self.sock.makefile("r", encoding="utf-8")
            while not self.over.is_set():
                line = reader.readline(65536 + 1)
                if not line or len(line) > 65536:
                    break
                message = decode_message(line)
                if message:
                    self.handle(message)
        except OSError:
            pass
        finally:
            if not self.over.is_set():
                with self.screen_lock:
                    print(paint("\n  Lost connection to host.", "1;31"))
                self.over.set()

    def ask_move(self):
        flush_stdin()
        is_direct = getattr(self.game_module, "direct_input", False)
        while not self.over.is_set():
            if is_direct:
                raw = read_direct_key(timeout=0.2)
                if raw is None:
                    continue
            else:
                raw = input().strip()

            if self.over.is_set() or not self.turn_event.is_set():
                return

            if str(raw).lower() in {"!ff", "!surrender", "!giveup", "!quit", "!exit", "ff", "surrender", "giveup", "quit", "exit", "resign"}:
                try:
                    self.send({"type": "surrender"})
                except OSError:
                    return
                return

            if str(raw).startswith("!"):
                msg = str(raw)[1:].strip()
                if msg.lower() in {"ff", "surrender", "giveup", "quit", "exit", "resign"}:
                    try:
                        self.send({"type": "surrender"})
                    except OSError:
                        return
                    return
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
        try:
            while not self.over.is_set():
                if self.turn_event.wait(0.15):
                    self.ask_move()
                elif self.match_ended:
                    # Match finished; wait for host to trigger rematch, or allow client to press Q to quit
                    key = read_direct_key(timeout=0.2)
                    if key is not None:
                        key_str = str(key).strip().upper()
                        if key_str in {"Q", "!FF", "QUIT", "EXIT"}:
                            self.over.set()
                            try:
                                self.send({"type": "surrender"})
                            except OSError:
                                pass
                            break
                        elif str(key).startswith("!"):
                            try:
                                self.send({"type": "chat", "text": str(key)[1:].strip()})
                            except OSError:
                                pass
                elif not self.started:
                    # Lobby waiting room
                    key = read_direct_key(timeout=0.2)
                    if key is not None:
                        key_str = str(key).strip().upper()
                        if key_str == "R":
                            try:
                                self.send({"type": "ready"})
                            except OSError:
                                pass
                        elif key_str in {"Q", "!FF", "QUIT", "EXIT"}:
                            self.over.set()
                            break
        except KeyboardInterrupt:
            self.over.set()
        finally:
            self.over.set()
            thread.join(timeout=0.5)


def join_lan_game():
    clear_screen()
    print(paint("=" * 56, "1;36"))
    print(paint("         JOIN A LAN GAME (AUTO-DISCOVERY)", "1;36"))
    print(paint("=" * 56, "1;36"))
    print("\n  🔍 Scanning local Wi-Fi / LAN for active games...")

    discovered = []
    try:
        discovered = discover_hosts(timeout=1.2)
    except Exception:
        discovered = []

    target_host = None
    target_port = DEFAULT_PORT

    if discovered:
        print(paint(f"\n  Found {len(discovered)} active LAN room(s):", "1;32"))
        for idx, r in enumerate(discovered, 1):
            r_name = r.get("room", "Game Room")
            g_name = r.get("game", "Game")
            p_cnt = r.get("players", 1)
            p_max = r.get("max", 4)
            r_ip = r.get("ip")
            r_port = r.get("port")
            print(f"    {idx}. {paint(r_name, '1;33')} — {g_name} ({p_cnt}/{p_max} players) [{r_ip}:{r_port}]")

        print("\n  Options:")
        print(f"    • Enter [1-{len(discovered)}] to connect to a discovered room")
        print("    • Enter 'M' for manual IP & port entry")
        print("    • Enter 'R' to rescan the network")
        print("    • Enter 'Q' to cancel and return to menu")

        choice = input("\nSelect option: ").strip()
        if not choice or choice.lower() in {"q", "quit", "cancel", "back", "exit"}:
            return
        if choice.lower() in {"r", "rescan"}:
            return join_lan_game()

        if choice.isdigit() and 1 <= int(choice) <= len(discovered):
            selected = discovered[int(choice) - 1]
            target_host = selected["ip"]
            target_port = selected["port"]
        elif choice.lower() == "m":
            target_host = None
        elif "." in choice:
            target_host = choice
        else:
            target_host = None
    else:
        print(paint("\n  [i] No active LAN game beacons detected on your subnet.", "2"))
        print("      You can enter the host IP manually or press 'R' to rescan.")
        quick_opt = input("\nEnter host IP (or 'R' to rescan, 'Q' to cancel): ").strip()
        if not quick_opt or quick_opt.lower() in {"q", "quit", "cancel", "back", "exit"}:
            return
        if quick_opt.lower() in {"r", "rescan"}:
            return join_lan_game()
        target_host = quick_opt

    if target_host is None:
        raw = input("\n  Host IP address (or ip:port, 'q' to cancel): ").strip()
        if not raw or raw.lower() in {"q", "quit", "cancel", "back", "exit"}:
            return
        if ":" in raw:
            parts = raw.split(":")
            target_host = parts[0]
            try:
                target_port = int(parts[1])
            except ValueError:
                target_port = DEFAULT_PORT
        else:
            target_host = raw
            port_raw = input(f"  Port [{DEFAULT_PORT}]: ").strip()
            target_port = int(port_raw) if port_raw else DEFAULT_PORT
    elif ":" in target_host:
        parts = target_host.split(":")
        target_host = parts[0]
        try:
            target_port = int(parts[1])
        except ValueError:
            pass
    elif target_port == DEFAULT_PORT and not discovered:
        port_raw = input(f"  Port [{DEFAULT_PORT}]: ").strip()
        target_port = int(port_raw) if port_raw else DEFAULT_PORT

    name = clean_name(input("  Your player name: "), "Guest")
    print(f"\n  Connecting to {target_host}:{target_port} ...")
    try:
        sock = socket.create_connection((target_host, target_port), timeout=10)
        sock.settimeout(None)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except (OSError, ValueError) as exc:
        print(paint(f"\n  [!] Could not connect to {target_host}:{target_port}: {exc}", "1;31"))
        print("      Make sure the host game has started and you are on the same Wi-Fi/LAN.")
        input("\n  Press Enter to return to main menu...")
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
