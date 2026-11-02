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


if __name__ == "__main__":
    unittest.main()
