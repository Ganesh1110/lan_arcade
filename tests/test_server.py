import json
import socket
import threading
import time
import unittest
from core.room import Room
from core.server import LanTCPServer
from games import connect4, bingo, liars_dice, battleship


class TestServerInit(unittest.TestCase):
    def test_room_initialization(self):
        for g in [bingo, connect4, liars_dice, battleship]:
            room = Room("TestHost", g)
            self.assertEqual(len(room.players), 1)
            self.assertEqual(room.players[0].name, "TestHost")
            self.assertTrue(room.players[0].is_host)
            self.assertEqual(room.game_module, g)

    def test_client_join_integration(self):
        room = Room("HostUser", connect4)
        server = LanTCPServer(("127.0.0.1", 0), room)
        port = server.server_address[1]

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=2.0)
            join_msg = json.dumps({"type": "join", "name": "FriendPlayer"}) + "\n"
            sock.sendall(join_msg.encode("utf-8"))

            reader = sock.makefile("r", encoding="utf-8")
            response_line = reader.readline()
            self.assertTrue(response_line)

            response = json.loads(response_line)
            self.assertEqual(response.get("type"), "joined")
            self.assertEqual(response.get("name"), "FriendPlayer")
            self.assertEqual(len(room.players), 2)
            sock.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
