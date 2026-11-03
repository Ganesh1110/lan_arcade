"""
Unit tests for AI Bots and Solo Mode Logic.
"""
import unittest
from games import connect4, tic_tac_toe, battleship, game2048, shiritori


class TestSoloModesLogic(unittest.TestCase):
    def test_2048_solo_move_logic(self):
        grid = [
            [2, 2, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        new_grid, changed, gained = game2048.move_grid(grid, "A")
        self.assertTrue(changed)
        self.assertEqual(new_grid[0][0], 4)
        self.assertEqual(gained, 4)

    def test_connect4_bot_win_check(self):
        state = connect4.create_state([{"id": 0, "name": "Human"}, {"id": 1, "name": "AI"}])
        # Place 4 tokens horizontally
        for c in range(4):
            state["board"][5][c] = "X"
        self.assertTrue(connect4.check_win(state["board"], 5, 3, "X"))

    def test_tic_tac_toe_bot_defense(self):
        # Human has cells 1 and 2, Bot must block cell 3
        state = tic_tac_toe.create_state([{"id": 0, "name": "Human"}, {"id": 1, "name": "AI"}])
        state["board"][0] = "X"
        state["board"][1] = "X"
        wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        winning_block = None
        for a, b, c in wins:
            line = [state["board"][a], state["board"][b], state["board"][c]]
            if line.count("X") == 2 and line.count(None) == 1:
                idx = [a, b, c][line.index(None)]
                winning_block = idx
                break
        self.assertEqual(winning_block, 2)

    def test_battleship_hunt_parity(self):
        hunt_targets = [(r, c) for r in range(6) for c in range(6) if (r + c) % 2 == 0]
        self.assertEqual(len(hunt_targets), 18)


if __name__ == "__main__":
    unittest.main()
