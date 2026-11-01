"""
Tracks player session information on the server.
"""
import threading


class PlayerSession:
    def __init__(self, player_id, name, socket=None, is_host=False):
        self.player_id = player_id
        self.name = name
        self.socket = socket
        self.is_host = is_host
        self.is_ready = True if is_host else False
        self.send_lock = threading.Lock()
        self.is_online = True
        self.wins = 0
        self.losses = 0

    def to_dict(self):
        return {
            "id": self.player_id,
            "name": self.name,
            "host": self.is_host,
            "ready": self.is_ready,
            "online": self.is_online,
            "wins": self.wins,
            "losses": self.losses,
        }
