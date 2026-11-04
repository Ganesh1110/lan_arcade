"""
Unit tests for Arrow Man Duel / Bowman Archery Game Module.
"""
import unittest
from games import arrow_man


class TestArrowMan(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "Archer1"}, {"id": 1, "name": "Archer2"}]
        self.state = arrow_man.create_state(self.sessions)

    def test_initial_state(self):
        self.assertEqual(len(self.state["players"]), 2)
        self.assertEqual(self.state["hp"][0], 100)
        self.assertEqual(self.state["hp"][1], 100)
        self.assertTrue(self.state["apples"][0])
        self.assertTrue(self.state["apples"][1])
        self.assertEqual(self.state["quivers"][0]["fire"], 1)
        self.assertEqual(self.state["quivers"][0]["bomb"], 1)

    def test_parse_action_standard_and_specials(self):
        valid, act = arrow_man.parse_action(self.state, 0, "45 70")
        self.assertTrue(valid)
        self.assertEqual(act["angle"], 45.0)
        self.assertEqual(act["power"], 70.0)
        self.assertEqual(act["arrow"], "standard")

        valid_f, act_f = arrow_man.parse_action(self.state, 0, "50 80 fire")
        self.assertTrue(valid_f)
        self.assertEqual(act_f["arrow"], "fire")

        valid_b, act_b = arrow_man.parse_action(self.state, 0, "b 55 85")
        self.assertTrue(valid_b)
        self.assertEqual(act_b["arrow"], "bomb")

    def test_parse_action_invalid_inputs(self):
        valid, err = arrow_man.parse_action(self.state, 0, "invalid")
        self.assertFalse(valid)

        # Negative power
        valid, err = arrow_man.parse_action(self.state, 0, "45 -10")
        self.assertFalse(valid)

        # Depleted quiver check
        self.state["quivers"][0]["fire"] = 0
        valid, err = arrow_man.parse_action(self.state, 0, "45 70 fire")
        self.assertFalse(valid)
        self.assertIn("remaining", err)

    def test_apply_action_deals_damage_and_records_trajectory(self):
        # Set zero wind for deterministic test
        self.state["wind"] = 0
        # Shoot an arrow
        arrow_man.apply_action(self.state, 0, {"angle": 45, "power": 70, "arrow": "standard"})
        self.assertTrue(len(self.state["trajectory"]) > 0)
        self.assertIsNotNone(self.state["last_shot"])
        self.assertEqual(self.state["turn_index"], 1)

    def test_quiver_decrements_on_special_shot(self):
        self.assertEqual(self.state["quivers"][0]["fire"], 1)
        arrow_man.apply_action(self.state, 0, {"angle": 45, "power": 60, "arrow": "fire"})
        self.assertEqual(self.state["quivers"][0]["fire"], 0)

    def test_is_over_when_hp_zero(self):
        self.state["hp"][1] = 0
        self.assertTrue(arrow_man.is_over(self.state))
        self.assertEqual(arrow_man.get_winner(self.state), ["Archer1"])

    def test_render_dashboard(self):
        v = arrow_man.view_for(self.state, 0)
        dashboard = arrow_man.render_dashboard(v)
        self.assertIn("A R R O W   M A N   D U E L", dashboard)
        self.assertIn("Archer1", dashboard)
        self.assertIn("Archer2", dashboard)
        self.assertIn("100 HP", dashboard)


if __name__ == "__main__":
    unittest.main()
