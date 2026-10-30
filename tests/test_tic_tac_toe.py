import unittest
from games import tic_tac_toe


class TestTicTacToe(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = tic_tac_toe.create_state(sessions)

    def test_win_condition(self):
        # P1 takes 1, 2, 3
        for cell in [1, 4, 2, 5, 3]: # P1: 1, 2, 3 ; P2: 4, 5
            curr = tic_tac_toe.current_player(self.state)
            valid, act = tic_tac_toe.parse_action(tic_tac_toe.view_for(self.state, curr), curr, str(cell))
            self.assertTrue(valid)
            tic_tac_toe.apply_action(self.state, curr, act)

        self.assertTrue(tic_tac_toe.is_over(self.state))
        self.assertEqual(tic_tac_toe.get_winner(self.state), ["P1"])


if __name__ == "__main__":
    unittest.main()
