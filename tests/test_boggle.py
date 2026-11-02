import unittest
from games import boggle


class TestBoggle(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = boggle.create_state(sessions)

    def test_pass_action_increments_passes(self):
        v0 = boggle.view_for(self.state, 0)
        valid, act = boggle.parse_action(v0, 0, "pass")
        self.assertTrue(valid)
        self.assertEqual(act, "PASS")

        boggle.apply_action(self.state, 0, act)
        self.assertEqual(self.state["consecutive_passes"], 1)

        boggle.apply_action(self.state, 1, "PASS")
        self.assertEqual(self.state["consecutive_passes"], 2)
        self.assertTrue(boggle.is_over(self.state))

    def test_invalid_word_rejected(self):
        v0 = boggle.view_for(self.state, 0)
        valid, err = boggle.parse_action(v0, 0, "XYZFAKEWORD")
        self.assertFalse(valid)
        self.assertIn("not recognized", err)


if __name__ == "__main__":
    unittest.main()
