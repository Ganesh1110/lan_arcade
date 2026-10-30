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
        self.send_lock = threading.Lock()
        self.is_online = True

    def to_dict(self):
        return {
            "id": self.player_id,
            "name": self.name,
            "host": self.is_host,
            "online": self.is_online,
        }
