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
    shiritori, game2048,
    boggle, mini_crossword, wordoku, scrabble_sprint, snake_and_ladder,
    chess_game, wordle, quiz_show, typing_racer,
    artillery, snake_duel, sonar
)


class TestServerInit(unittest.TestCase):
    def test_room_initialization(self):
        for g in [
            bingo, connect4, hangman, battleship, shiritori, game2048,
            boggle, mini_crossword, wordoku, scrabble_sprint, snake_and_ladder,
            chess_game, wordle, quiz_show, typing_racer,
            artillery, snake_duel, sonar
        ]:
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
        except (PermissionError, OSError) as e:
            server.shutdown()
            server.server_close()
            self.skipTest(f"Socket connection restricted in environment: {e}")

        try:
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
            thread.join(timeout=1.0)
            sys.stdout.flush()


class MockSocket:
    def __init__(self):
        self.sent_bytes = b""

    def sendall(self, data):
        self.sent_bytes += data

    def close(self):
        pass


class TestRematchFlow(unittest.TestCase):
    def test_client_rematch_lifecycle(self):
        from core.client import ClientSession
        mock_sock = MockSocket()
        session = ClientSession(mock_sock, "JoinedPlayer")

        # 1. Join and game start
        session.handle({"type": "joined", "player_id": 1, "name": "JoinedPlayer"})
        self.assertEqual(session.my_id, 1)

        start_msg = {
            "type": "start",
            "game_id": "connect4",
            "you": 1,
            "name": "JoinedPlayer",
            "view": {},
            "players": [{"id": 0, "name": "HostUser"}, {"id": 1, "name": "JoinedPlayer"}]
        }
        session.handle(start_msg)
        self.assertTrue(session.started)
        self.assertFalse(session.match_ended)
        self.assertFalse(session.over.is_set())

        # 2. Match completes
        end_msg = {
            "type": "end",
            "message": "Winner(s): HostUser",
            "winners": ["HostUser"],
            "players": [{"id": 0, "name": "HostUser"}, {"id": 1, "name": "JoinedPlayer"}]
        }
        session.handle(end_msg)
        self.assertTrue(session.match_ended)
        # Client MUST NOT terminate connection on match end so rematch can happen!
        self.assertFalse(session.over.is_set())

        # 3. Host triggers rematch
        rematch_msg = {"type": "rematch", "message": "Host initiated a rematch!"}
        session.handle(rematch_msg)
        self.assertFalse(session.match_ended)
        self.assertFalse(session.over.is_set())

        # 4. New round begins
        session.handle(start_msg)
        self.assertTrue(session.started)
        self.assertFalse(session.match_ended)
        self.assertFalse(session.over.is_set())

        # 5. Host returns to main menu
        session.handle({"type": "host_exit", "message": "Host returned to main menu."})
        self.assertTrue(session.over.is_set())


if __name__ == "__main__":
    unittest.main()
