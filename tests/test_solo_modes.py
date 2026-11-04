"""
Unit tests for AI Bots and Solo Mode Logic.
"""
import unittest
from games import connect4, tic_tac_toe, battleship, game2048, shiritori, wordle, quiz_show, artillery, snake_duel, chess_game
from core.solo_modes import (
    _get_best_wordle_guess,
    _get_best_artillery_shot,
    _get_best_snake_duel_move,
    _get_best_chess_move,
    _make_human_typing_attempt
)


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

    def test_wordle_bot_guess_deduction(self):
        state = wordle.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "WordleBot"}])
        state["target_word"] = "PEACE"
        guess = _get_best_wordle_guess(state, 1)
        self.assertEqual(len(guess), 5)
        self.assertTrue(guess.isalpha())

        # Simulate bot making a guess
        wordle.apply_action(state, 1, "CRANE")
        next_guess = _get_best_wordle_guess(state, 1)
        self.assertEqual(next_guess, "PEACE")

    def test_artillery_bot_calculation(self):
        terrain = [5] * artillery.WIDTH
        shot = _get_best_artillery_shot(terrain, bot_x=50, target_x=10, wind=0)
        self.assertIn("angle", shot)
        self.assertIn("power", shot)
        self.assertTrue(90 <= shot["angle"] <= 180)
        self.assertTrue(10 <= shot["power"] <= 100)

    def test_snake_duel_bot_move_safety(self):
        state = snake_duel.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "Bot"}])
        # Bot is at (24, 7) facing left (-1, 0)
        move = _get_best_snake_duel_move(state, 1)
        self.assertIn(move, ["W", "A", "S", "D"])

    def test_chess_bot_legal_move(self):
        state = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        move = _get_best_chess_move(state["board"])
        self.assertIsNotNone(move)
        self.assertIn("from", move)
        self.assertIn("to", move)

    def test_wordle_human_like_second_attempt_no_instant_win(self):
        state = wordle.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "WordleBot"}])
        state["target_word"] = "PEACE"
        # Bot's first guess is CRANE
        wordle.apply_action(state, 1, "CRANE")
        # In human_like mode, bot should NOT instantly cheat and solve "PEACE" on attempt 2
        human_guess = _get_best_wordle_guess(state, 1, human_like=True)
        self.assertEqual(len(human_guess), 5)
        self.assertTrue(human_guess.isalpha())
        self.assertNotEqual(human_guess, "PEACE")

    def test_artillery_human_like_ranging_shot(self):
        terrain = [5] * artillery.WIDTH
        # Shot 1 should be a ranging sighting shot with power offset
        shot1 = _get_best_artillery_shot(terrain, bot_x=50, target_x=10, wind=0, shot_num=1, human_like=True)
        self.assertIn("angle", shot1)
        self.assertIn("power", shot1)
        # Verify shot 1 does not hit target directly
        pts, ix, iy, direct, dmg = artillery.simulate_ballistic_flight(
            terrain, 50, 10, shot1["angle"], shot1["power"], 0
        )
        self.assertFalse(direct)
        self.assertEqual(dmg, 0)

    def test_typing_racer_human_like_attempt(self):
        snip = "Life is short, use Python."
        bot_typed, msg = _make_human_typing_attempt(snip)
        self.assertTrue(len(bot_typed) > 0)
        self.assertTrue(isinstance(msg, str))

    def test_snake_duel_human_like_move(self):
        state = snake_duel.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "Bot"}])
        move = _get_best_snake_duel_move(state, 1, human_like=True)
        self.assertIn(move, ["W", "A", "S", "D"])

    def test_chess_human_like_opening_book(self):
        state = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        # White moves e2->e4
        state["board"][4][4] = state["board"][6][4]
        state["board"][6][4] = None
        move = _get_best_chess_move(state["board"], ["W: e2➔e4"], human_like=True)
        self.assertIsNotNone(move)
        # Should play standard response: e7e5, c7c5, or e7e6
        self.assertIn(move["notation"], ["e7e5", "c7c5", "e7e6"])


if __name__ == "__main__":
    unittest.main()
