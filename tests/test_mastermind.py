import unittest
from games import mastermind


class TestMastermind(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "Codemaker"}, {"id": 1, "name": "Codebreaker"}]
        self.state = mastermind.create_state(sessions)

    def test_set_code_and_crack(self):
        # Codemaker sets 1 2 3 4
        v0 = mastermind.view_for(self.state, 0)
        valid, digits = mastermind.parse_action(v0, 0, "1 2 3 4")
        self.assertTrue(valid)
        mastermind.apply_action(self.state, 0, digits)

        # Codebreaker guesses 1 2 3 4
        v1 = mastermind.view_for(self.state, 1)
        valid, guess = mastermind.parse_action(v1, 1, "1 2 3 4")
        self.assertTrue(valid)
        mastermind.apply_action(self.state, 1, guess)

        self.assertTrue(mastermind.is_over(self.state))
        self.assertEqual(mastermind.get_winner(self.state), ["Codebreaker"])


if __name__ == "__main__":
    unittest.main()
