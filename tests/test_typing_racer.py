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
        snip = typing_racer.get_current_snippet(self.state)
        # Accurate input earns +35% boost
        typing_racer.apply_action(self.state, 0, snip)
        self.assertEqual(self.state["progress"][0], 35)

    def test_winning_condition(self):
        self.state["progress"][0] = 100
        self.assertTrue(typing_racer.is_over(self.state))
        self.assertEqual(typing_racer.get_winner(self.state), ["Speedy"])

    def test_dynamic_snippets_generation(self):
        playlist1 = typing_racer.generate_dynamic_snippets(12)
        playlist2 = typing_racer.generate_dynamic_snippets(12)
        self.assertEqual(len(playlist1), 12)
        self.assertEqual(len(playlist2), 12)
        # All items are non-empty strings
        for s in playlist1:
            self.assertIsInstance(s, str)
            self.assertTrue(len(s) > 0)

    def test_procedural_snippet_generation(self):
        procedural = typing_racer.generate_procedural_snippet()
        self.assertIsInstance(procedural, str)
        self.assertTrue(len(procedural) > 10)

    def test_create_state_randomized_snippets(self):
        st1 = typing_racer.create_state(self.sessions, randomize=True)
        st2 = typing_racer.create_state(self.sessions, randomize=True)
        self.assertIn("snippets", st1)
        self.assertIn("snippets", st2)
        self.assertEqual(len(st1["snippets"]), 12)


if __name__ == "__main__":
    unittest.main()
