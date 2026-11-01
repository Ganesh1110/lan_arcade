"""
Room class manages connected sessions, lobby state, thread safety, and move queues.
"""
import json
import queue
import socket
import threading
from collections import deque
from config import MAX_PLAYERS
from core.session import PlayerSession
from protocol import decode_message, encode_message
from utils.validation import clean_name


class Room:
    def __init__(self, host_name, game_module):
        self.lock = threading.RLock()
        self.game_module = game_module
        self.max_players = getattr(game_module, "max_players", MAX_PLAYERS)
        self.min_players = getattr(game_module, "min_players", 2)

        # Host is player_id = 0
        host_session = PlayerSession(0, host_name, is_host=True)
        self.players = [host_session]
        self.next_id = 1

        self.connections = {}      # pid -> socket
        self.send_locks = {}       # pid -> Lock
        self.incoming_moves = queue.Queue()

        self.started = False
        self.closed = False
        self.ended = False
        self.log = deque(maxlen=6)

    def get_player(self, pid):
        with self.lock:
            for p in self.players:
                if p.player_id == pid:
                    return p
            return None

    def unique_name(self, name):
        with self.lock:
            taken = {p.name.lower() for p in self.players}
            if name.lower() not in taken:
                return name
            n = 2
            while f"{name} ({n})".lower() in taken:
                n += 1
            return f"{name} ({n})"

    def toggle_ready(self, pid):
        with self.lock:
            player = self.get_player(pid)
            if player and not player.is_host:
                player.is_ready = not player.is_ready
                return player.is_ready
            return True

    def add_client(self, name, sock):
        with self.lock:
            if self.closed:
                return None, "The host has closed the room."
            if self.started:
                return None, "The game has already started."
            if len(self.players) >= self.max_players:
                return None, f"The room is full ({self.max_players}/{self.max_players})."

            pid = self.next_id
            self.next_id += 1
            session = PlayerSession(pid, self.unique_name(name), socket=sock)
            self.players.append(session)
            self.connections[pid] = sock
            self.send_locks[pid] = threading.Lock()
            return pid, None

    def disconnect(self, pid):
        with self.lock:
            self.connections.pop(pid, None)
            self.send_locks.pop(pid, None)
            player = self.get_player(pid)
            if player is not None:
                player.is_online = False
                if not self.started:
                    self.players = [p for p in self.players if p.player_id != pid]
            return player

    def send(self, pid, payload):
        with self.lock:
            sock = self.connections.get(pid)
            send_lock = self.send_locks.get(pid)
        if sock is None or send_lock is None:
            return False
        data = encode_message(payload)
        try:
            with send_lock:
                sock.sendall(data)
            return True
        except OSError:
            return False

    def broadcast(self, payload):
        with self.lock:
            pids = list(self.connections.keys())
        for pid in pids:
            self.send(pid, payload)

    def player_names(self):
        with self.lock:
            return [p.name for p in self.players]

    def lobby_payload(self):
        with self.lock:
            return [
                {
                    "name": p.name,
                    "ready": p.is_ready,
                    "host": p.is_host,
                    "id": p.player_id
                }
                for p in self.players
            ]

    def players_payload(self):
        with self.lock:
            return [p.to_dict() for p in self.players]

    def drain_moves(self):
        while True:
            try:
                self.incoming_moves.get_nowait()
            except queue.Empty:
                return

    def client_handler(self, sock):
        pid = None
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.settimeout(10)
            reader = sock.makefile("r", encoding="utf-8")
            first = reader.readline()
            if not first:
                return

            request = decode_message(first)
            if not request or request.get("type") != "join":
                sock.sendall(encode_message({"type": "reject", "message": "Expected join request."}))
                return

            sock.settimeout(None)
            raw_name = request.get("name", "Guest")
            pid, reason = self.add_client(clean_name(raw_name, "Guest"), sock)
            if pid is None:
                sock.sendall(encode_message({"type": "reject", "message": reason}))
                return

            player = self.get_player(pid)
            self.send(pid, {
                "type": "joined",
                "player_id": pid,
                "name": player.name,
                "max": self.max_players
            })

            try:
                where = sock.getpeername()[0]
            except OSError:
                where = "?"

            names = self.player_names()
            print(f"\n  + {player.name} joined from {where} ({len(names)}/{self.max_players} players: {', '.join(names)})")
            self.broadcast({"type": "lobby", "players": self.lobby_payload()})

            for line in reader:
                message = decode_message(line)
                if not message:
                    continue
                kind = message.get("type")

                if kind == "ready":
                    self.toggle_ready(pid)
                    self.broadcast({"type": "lobby", "players": self.lobby_payload()})
                elif kind == "chat":
                    chat_text = str(message.get("text", "")).strip()[:100]
                    if chat_text:
                        entry = f"💬 {player.name}: {chat_text}"
                        self.log.append(entry)
                        self.broadcast({"type": "chat", "sender": player.name, "text": chat_text, "entry": entry})
                elif kind == "action":
                    self.incoming_moves.put((pid, message.get("action")))
        except (OSError, ValueError):
            pass
        finally:
            if pid is not None:
                player = self.disconnect(pid)
                if player is not None and not self.closed:
                    if not self.started:
                        names = self.player_names()
                        print(f"\n  - {player.name} left the lobby ({len(names)}/{self.max_players} players).")
                        self.broadcast({"type": "lobby", "players": self.lobby_payload()})
                    else:
                        text = f"{player.name} left the game."
                        print(f"\n  - {text}")
                        self.log.append(text)
                        self.broadcast({"type": "notice", "message": text, "players": self.players_payload()})
            try:
                sock.close()
            except OSError:
                pass
