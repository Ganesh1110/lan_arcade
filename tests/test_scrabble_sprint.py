import unittest
from games import scrabble_sprint


class TestScrabbleSprint(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = scrabble_sprint.create_state(sessions)

    def test_pass_and_reroll(self):
        v0 = scrabble_sprint.view_for(self.state, 0)
        valid, act = scrabble_sprint.parse_action(v0, 0, "pass")
        self.assertTrue(valid)
        self.assertEqual(act, "PASS")

        scrabble_sprint.apply_action(self.state, 0, act)
        self.assertEqual(self.state["consecutive_passes"], 1)

        valid_r, act_r = scrabble_sprint.parse_action(v0, 1, "reroll")
        self.assertTrue(valid_r)
        self.assertEqual(act_r, "REROLL")

        old_rack = list(self.state["rack"])
        scrabble_sprint.apply_action(self.state, 1, act_r)
        self.assertEqual(self.state["consecutive_passes"], 0)


if __name__ == "__main__":
    unittest.main()
