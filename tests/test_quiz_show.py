"""
Unit tests for College Quiz Show Game Module.
"""
import unittest
from games import quiz_show


class TestQuizShow(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "QuizMaster"}, {"id": 1, "name": "Rival"}]
        self.state = quiz_show.create_state(self.sessions)

    def test_initial_state(self):
        self.assertEqual(len(self.state["questions"]), quiz_show.TOTAL_ROUNDS)
        self.assertEqual(self.state["scores"][0], 0)
        self.assertEqual(self.state["streaks"][0], 0)
        self.assertEqual(quiz_show.current_player(self.state), 0)

    def test_correct_answer_scores_and_streaks(self):
        # Force first question
        q0 = self.state["questions"][0]
        correct_ans = q0["answer"]

        valid, choice = quiz_show.parse_action(self.state, 0, correct_ans.lower())
        self.assertTrue(valid)

        quiz_show.apply_action(self.state, 0, choice)
        self.assertEqual(self.state["scores"][0], 100)
        self.assertEqual(self.state["streaks"][0], 1)
        self.assertEqual(self.state["current_round"], 1)

    def test_incorrect_answer_resets_streak(self):
        self.state["streaks"][0] = 3
        q0 = self.state["questions"][0]
        wrong_ans = "A" if q0["answer"] != "A" else "B"

        quiz_show.apply_action(self.state, 0, wrong_ans)
        self.assertEqual(self.state["streaks"][0], 0)


if __name__ == "__main__":
    unittest.main()
