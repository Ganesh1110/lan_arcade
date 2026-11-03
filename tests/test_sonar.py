"""
Unit tests for Submarine Radar Hunt (Sonar) Game Module.
"""
import unittest
from games import sonar


class TestSonarSubmarine(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "SubCmdr1"}, {"id": 1, "name": "SubCmdr2"}]
        self.state = sonar.create_state(self.sessions)

    def test_initial_state(self):
        self.assertEqual(self.state["hp"][0], 3)
        self.assertEqual(self.state["hp"][1], 3)
        self.assertEqual(self.state["torpedoes"][0], 4)
        self.assertEqual(self.state["pings"][0], 3)

    def test_parse_action_commands(self):
        valid_m, act_m = sonar.parse_action(self.state, 0, "MOVE N")
        self.assertTrue(valid_m)
        self.assertEqual(act_m["action"], "move")
        self.assertEqual(act_m["dir"], "N")

        valid_s, act_s = sonar.parse_action(self.state, 0, "SONAR E")
        self.assertTrue(valid_s)
        self.assertEqual(act_s["action"], "sonar")
        self.assertEqual(act_s["target"], "E")

        valid_t, act_t = sonar.parse_action(self.state, 0, "TORPEDO E4")
        self.assertTrue(valid_t)
        self.assertEqual(act_t["action"], "torpedo")
        self.assertEqual(act_t["coord"], (3, 4))

    def test_direct_torpedo_hit(self):
        # Place opponent at E4 (row 3 col 4) and fire torpedo at E4
        self.state["positions"][1] = (3, 4)
        act = {"action": "torpedo", "coord": (3, 4), "text": "E4"}
        sonar.apply_action(self.state, 0, act)
        # Direct hit takes 2 damage from 3 HP -> 1 HP
        self.assertEqual(self.state["hp"][1], 1)


if __name__ == "__main__":
    unittest.main()
