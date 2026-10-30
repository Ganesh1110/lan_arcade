import unittest
from games import connect4


class TestConnectFour(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "Player 1"}, {"id": 1, "name": "Player 2"}]
        self.state = connect4.create_state(sessions)

    def test_drop_token(self):
        valid, col_idx = connect4.parse_action(self.state, 0, "3")
        self.assertTrue(valid)
        self.assertEqual(col_idx, 2)

        connect4.apply_action(self.state, 0, col_idx)
        self.assertEqual(self.state["board"][5][2], "X")

    def test_horizontal_win(self):
        # Drop X in cols 1, 2, 3, 4
        for c in range(1, 4):
            connect4.apply_action(self.state, 0, c - 1)  # X drops
            connect4.apply_action(self.state, 1, 6)      # O drops in col 7

        # Winning drop in col 4
        connect4.apply_action(self.state, 0, 3)
        self.assertTrue(connect4.is_over(self.state))
        self.assertEqual(connect4.get_winner(self.state), ["Player 1"])


if __name__ == "__main__":
    unittest.main()
