import unittest
from core.room import Room, SURRENDER_COMMANDS
from games import bingo


class TestSurrenderCommands(unittest.TestCase):
    def test_surrender_command_set(self):
        self.assertIn("!ff", SURRENDER_COMMANDS)
        self.assertIn("!surrender", SURRENDER_COMMANDS)
        self.assertIn("!giveup", SURRENDER_COMMANDS)
        self.assertIn("ff", SURRENDER_COMMANDS)
        self.assertIn("surrender", SURRENDER_COMMANDS)
        self.assertIn("giveup", SURRENDER_COMMANDS)

    def test_room_surrender_queue(self):
        room = Room("HostPlayer", bingo)
        self.assertTrue(room.surrender_queue.empty())
        room.surrender_queue.put(0)
        self.assertFalse(room.surrender_queue.empty())
        pid = room.surrender_queue.get()
        self.assertEqual(pid, 0)

    def test_surrender_in_multiplayer_match_and_flag_reset(self):
        from unittest.mock import patch
        from core.session import PlayerSession
        from core.game_manager import GameManager
        from core.server import handle_surrender

        room = Room("Host", bingo)
        p1 = PlayerSession(1, "Player1")
        p2 = PlayerSession(2, "Player2")
        room.players.extend([p1, p2])
        gm = GameManager(bingo)
        gm.initialize(room.players)

        # Host surrenders in 3-player match
        is_over = handle_surrender(room, gm, 0)
        self.assertFalse(is_over)
        self.assertTrue(room.get_player(0).has_surrendered)
        self.assertFalse(room.get_player(1).has_surrendered)
        self.assertFalse(room.get_player(2).has_surrendered)

        # Player 1 surrenders: leaving only Player 2 -> now match is over and Player 2 wins
        with patch("builtins.input", return_value="2"):
            is_over2 = handle_surrender(room, gm, 1)
        self.assertTrue(is_over2)
        self.assertTrue(room.get_player(1).has_surrendered)
        self.assertEqual(room.get_player(2).wins, 1)

        # Start of next game / rematch: all flags reset
        for p in room.players:
            p.has_surrendered = False

        self.assertFalse(room.get_player(0).has_surrendered)
        self.assertFalse(room.get_player(1).has_surrendered)
        self.assertFalse(room.get_player(2).has_surrendered)


if __name__ == "__main__":
    unittest.main()
