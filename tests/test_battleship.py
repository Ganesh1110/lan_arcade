import unittest
from games import battleship


class TestBattleship(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = battleship.create_state(sessions)

    def test_coordinate_parsing(self):
        v = battleship.view_for(self.state, 0)
        valid, coord = battleship.parse_action(v, 0, "C3")
        self.assertTrue(valid)
        self.assertEqual(coord, (2, 2))  # Row 3 -> index 2, Col C -> index 2

    def test_attack_and_repeat(self):
        v = battleship.view_for(self.state, 0)
        valid, coord = battleship.parse_action(v, 0, "A1")
        battleship.apply_action(self.state, 0, coord)

        # Update view
        v_updated = battleship.view_for(self.state, 0)
        valid_again, err = battleship.parse_action(v_updated, 0, "A1")
        self.assertFalse(valid_again)
        self.assertIn("already attacked", err)


if __name__ == "__main__":
    unittest.main()
