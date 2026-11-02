import unittest
from games import hangman


class TestHangman(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "Wordmaster"}, {"id": 1, "name": "Guesser"}]
        self.state = hangman.create_state(sessions)

    def test_wordmaster_sets_word(self):
        self.assertEqual(hangman.current_player(self.state), 0)
        valid, word = hangman.parse_action(self.state, 0, "PLANET")
        self.assertTrue(valid)
        hangman.apply_action(self.state, 0, word)

        self.assertEqual(self.state["secret_word"], "PLANET")
        self.assertEqual(hangman.current_player(self.state), 1)

    def test_guesser_view_privacy_and_revealed_pattern(self):
        hangman.apply_action(self.state, 0, "PLANET")

        v_guesser = hangman.view_for(self.state, 1)
        self.assertIsNone(v_guesser["secret_word"])
        self.assertEqual(v_guesser["revealed_pattern"], "_ _ _ _ _ _")
        self.assertEqual(v_guesser["word_len"], 6)

        # Guesser guesses 'E'
        valid, guess = hangman.parse_action(v_guesser, 1, "E")
        self.assertTrue(valid)
        hangman.apply_action(self.state, 1, guess)

        v_guesser2 = hangman.view_for(self.state, 1)
        self.assertEqual(v_guesser2["revealed_pattern"], "_ _ _ _ E _")
        self.assertIsNone(v_guesser2["secret_word"])

    def test_guesser_full_word_instant_win(self):
        hangman.apply_action(self.state, 0, "PLANET")
        valid, guess = hangman.parse_action(self.state, 1, "PLANET")
        self.assertTrue(valid)
        hangman.apply_action(self.state, 1, guess)

        self.assertTrue(hangman.is_over(self.state))
        self.assertEqual(hangman.get_winner(self.state), ["Guesser"])


if __name__ == "__main__":
    unittest.main()
