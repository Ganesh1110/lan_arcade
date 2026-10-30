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


if __name__ == "__main__":
    unittest.main()
