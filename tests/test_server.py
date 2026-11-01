import json
import socket
import sys
import threading
import time
import unittest
from core.game_manager import GameManager
from core.room import Room
from core.server import LanTCPServer
from games import (
    connect4, bingo, hangman, battleship,
    rock_paper_scissors, shiritori, game2048, number_duel,
    boggle, mini_crossword, wordoku, scrabble_sprint
)


class TestServerInit(unittest.TestCase):
    def test_room_initialization(self):
        for g in [bingo, connect4, hangman, battleship, rock_paper_scissors, shiritori, game2048, number_duel, boggle, mini_crossword, wordoku, scrabble_sprint]:
            room = Room("TestHost", g)
            self.assertEqual(len(room.players), 1)
            self.assertEqual(room.players[0].name, "TestHost")
            self.assertTrue(room.players[0].is_host)
            self.assertEqual(room.game_module, g)

    def test_game_manager_apply_action(self):
        gm = GameManager(connect4)
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        gm.initialize(sessions)

        valid, action_data = connect4.parse_action(gm.state, 0, "3")
        self.assertTrue(valid)

        events = gm.apply_action(0, action_data)
        self.assertIn("log", events)
        self.assertIn("column 3", events["log"][0])

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
            sys.stdout.flush()
            time.sleep(0.1)


if __name__ == "__main__":
    unittest.main()
