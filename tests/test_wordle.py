"""
Unit tests for Wordle Versus Game Module.
"""
import unittest
from games import wordle


class TestWordleVersus(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "PlayerA"}, {"id": 1, "name": "PlayerB"}]
        self.state = wordle.create_state(self.sessions)
        self.state["target_word"] = "CRANE"

    def test_evaluate_guess(self):
        # Target: CRANE, Guess: CRATE -> C:green, R:green, A:green, T:gray, E:green
        eval_res = wordle.evaluate_guess("CRANE", "CRATE")
        statuses = [st for _, st in eval_res]
        self.assertEqual(statuses, ["green", "green", "green", "gray", "green"])

    def test_yellow_letter_evaluation(self):
        # Target: CRANE, Guess: OCEAN -> O:gray, C:yellow, E:yellow, A:yellow, N:yellow
        eval_res = wordle.evaluate_guess("CRANE", "OCEAN")
        statuses = [st for _, st in eval_res]
        self.assertEqual(statuses, ["gray", "yellow", "yellow", "yellow", "yellow"])

    def test_exact_solve_wins_game(self):
        valid, act = wordle.parse_action(self.state, 0, "CRANE")
        self.assertTrue(valid)

        wordle.apply_action(self.state, 0, act)
        self.assertTrue(self.state["solved"][0])
        self.assertTrue(wordle.is_over(self.state))
        self.assertEqual(wordle.get_winner(self.state), ["PlayerA"])

    def test_invalid_length_guess(self):
        valid, err = wordle.parse_action(self.state, 0, "CAT")
        self.assertFalse(valid)
        self.assertIn("5 letters", err)


if __name__ == "__main__":
    unittest.main()
