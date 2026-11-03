"""
Unit tests for Artillery Duel / Pocket Tanks Game Module.
"""
import unittest
from games import artillery


class TestArtilleryDuel(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "Tanker1"}, {"id": 1, "name": "Tanker2"}]
        self.state = artillery.create_state(self.sessions)

    def test_terrain_generation(self):
        terrain = self.state["terrain"]
        self.assertEqual(len(terrain), artillery.WIDTH)
        for h in terrain:
            self.assertGreaterEqual(h, 2)
            self.assertLessEqual(h, artillery.HEIGHT)

    def test_parse_action_valid(self):
        valid, act = artillery.parse_action(self.state, 0, "45 70")
        self.assertTrue(valid)
        self.assertEqual(act["angle"], 45.0)
        self.assertEqual(act["power"], 70.0)

    def test_parse_action_invalid_range(self):
        valid, err = artillery.parse_action(self.state, 0, "200 50")
        self.assertFalse(valid)
        self.assertIn("180", err)

    def test_apply_action_fires_shot(self):
        res = artillery.apply_action(self.state, 0, {"angle": 45, "power": 60})
        self.assertIn("log", res)
        self.assertIsNotNone(self.state["last_shot"])
        self.assertGreater(len(self.state["trajectory"]), 0)
        self.assertEqual(artillery.current_player(self.state), 1)


if __name__ == "__main__":
    unittest.main()
