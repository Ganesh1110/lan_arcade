"""
Room class manages connected sessions, lobby state, thread safety, and move queues.
"""
import json
import queue
import threading
from collections import deque
from config import MAX_PLAYERS
from core.session import PlayerSession
from protocol import encode_message


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

    def players_payload(self):
        with self.lock:
            return [p.to_dict() for p in self.players]

    def drain_moves(self):
        while True:
            try:
                self.incoming_moves.get_nowait()
            except queue.Empty:
                return
