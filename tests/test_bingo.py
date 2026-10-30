import unittest
from games import bingo


class TestBingo(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "Host"}, {"id": 1, "name": "Guest"}]
        self.state = bingo.create_state(sessions)

    def test_initial_state(self):
        self.assertEqual(len(self.state["players"]), 2)
        self.assertEqual(len(self.state["called"]), 0)
        self.assertIsNone(self.state["winner"])

    def test_call_number(self):
        valid, res = bingo.parse_action(self.state, 0, "12")
        self.assertTrue(valid)
        self.assertEqual(res, 12)

        events = bingo.apply_action(self.state, 0, 12)
        self.assertIn(12, self.state["called"])
        self.assertEqual(self.state["turn_index"], 1)

    def test_duplicate_call(self):
        bingo.apply_action(self.state, 0, 5)
        valid, err = bingo.parse_action(self.state, 1, "5")
        self.assertFalse(valid)
        self.assertIn("already called", err)


if __name__ == "__main__":
    unittest.main()
