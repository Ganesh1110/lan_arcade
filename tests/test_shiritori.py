import unittest
from games import shiritori


class TestShiritoriLives(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = shiritori.create_state(self.sessions)

    def test_valid_word_advances_turn(self):
        shiritori.apply_action(self.state, 0, "APPLE")
        self.assertEqual(self.state["last_word"], "APPLE")
        self.assertEqual(self.state["required_letter"], "E")
        self.assertEqual(self.state["lives"][0], 3)
        self.assertEqual(shiritori.current_player(self.state), 1)

    def test_wrong_starting_letter_deducts_life(self):
        shiritori.apply_action(self.state, 0, "APPLE")
        self.assertEqual(shiritori.current_player(self.state), 1)
        # P2 enters "BANANA" instead of starting with "E"
        events = shiritori.apply_action(self.state, 1, "BANANA")
        self.assertEqual(self.state["lives"][1], 2)
        self.assertIn("Wrong starting letter", events["log"][0])

    def test_duplicate_word_deducts_life(self):
        shiritori.apply_action(self.state, 0, "TIGER")     # Last letter R
        shiritori.apply_action(self.state, 1, "RABBIT")    # Last letter T
        # P1 enters "TIGER" which starts with T, but was already used!
        events = shiritori.apply_action(self.state, 0, "TIGER")
        self.assertEqual(self.state["lives"][0], 2)
        self.assertIn("Already used word", events["log"][0])


if __name__ == "__main__":
    unittest.main()
