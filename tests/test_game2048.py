import unittest
from games import game2048


class TestGame2048(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "Host"}, {"id": 1, "name": "Guest"}]
        self.state = game2048.create_state(sessions)

    def test_slide_and_merge(self):
        line = [2, 2, 4, 8]
        merged, gain = game2048.slide_and_merge_line(line)
        self.assertEqual(merged, [4, 4, 8, 0])
        self.assertEqual(gain, 4)

    def test_can_move_full_board(self):
        full_no_moves = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2]
        ]
        self.assertFalse(game2048.can_move(full_no_moves))

        full_with_moves = [
            [2, 2, 4, 8],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2]
        ]
        self.assertTrue(game2048.can_move(full_with_moves))

    def test_locked_out_ends_game(self):
        self.state["boards"][0] = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2]
        ]
        self.state["boards"][1] = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2]
        ]
        # Trigger apply_action to detect lockout
        game2048.apply_action(self.state, 0, "W")
        game2048.apply_action(self.state, 1, "W")
        self.assertTrue(game2048.is_over(self.state))


if __name__ == "__main__":
    unittest.main()
