"""
Unit tests for Typing Racer Game Module.
"""
import unittest
from games import typing_racer


class TestTypingRacer(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "Speedy"}, {"id": 1, "name": "Racer"}]
        self.state = typing_racer.create_state(self.sessions)

    def test_calculate_accuracy(self):
        acc = typing_racer.calculate_accuracy("Hello World", "Hello World")
        self.assertEqual(acc, 100.0)

        # 1 typo
        acc_typo = typing_racer.calculate_accuracy("Hello World", "Hella World")
        self.assertAlmostEqual(acc_typo, 90.9, places=1)

    def test_apply_action_advances_progress(self):
        snip = typing_racer.TARGET_SNIPPETS[0]
        # Accurate input earns +35% boost
        typing_racer.apply_action(self.state, 0, snip)
        self.assertEqual(self.state["progress"][0], 35)

    def test_winning_condition(self):
        self.state["progress"][0] = 100
        self.assertTrue(typing_racer.is_over(self.state))
        self.assertEqual(typing_racer.get_winner(self.state), ["Speedy"])


if __name__ == "__main__":
    unittest.main()
