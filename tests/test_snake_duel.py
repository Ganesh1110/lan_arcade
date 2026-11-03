"""
Unit tests for Snake Duel / Tron Lightcycles Game Module.
"""
import unittest
from games import snake_duel


class TestSnakeDuel(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "Cycle1"}, {"id": 1, "name": "Cycle2"}]
        self.state = snake_duel.create_state(self.sessions)

    def test_initial_state(self):
        self.assertEqual(len(self.state["players"]), 2)
        self.assertTrue(self.state["alive"][0])
        self.assertTrue(self.state["alive"][1])
        self.assertEqual(len(self.state["trails"][0]), 1)
        self.assertEqual(len(self.state["trails"][1]), 1)

    def test_parse_action_cardinal_and_relative(self):
        valid_w, act_w = snake_duel.parse_action(self.state, 0, "W")
        self.assertTrue(valid_w)
        self.assertEqual(act_w, "W")

        valid_l, act_l = snake_duel.parse_action(self.state, 0, "L")
        self.assertTrue(valid_l)
        self.assertEqual(act_l, "L")

    def test_apply_action_moves_and_leaves_trail(self):
        start_x, start_y = self.state["positions"][0]
        # P1 moves Up (W)
        snake_duel.apply_action(self.state, 0, "W")
        new_x, new_y = self.state["positions"][0]
        self.assertEqual((new_x, new_y), (start_x, start_y - 1))
        self.assertEqual(len(self.state["trails"][0]), 2)

    def test_wall_collision_causes_crash(self):
        # Place player 0 at top wall (y=0) and steer Up (W)
        self.state["positions"][0] = (10, 0)
        self.state["directions"][0] = (0, -1)
        snake_duel.apply_action(self.state, 0, "W")
        self.assertFalse(self.state["alive"][0])
        self.assertTrue(snake_duel.is_over(self.state))
        self.assertEqual(snake_duel.get_winner(self.state), ["Cycle2"])


if __name__ == "__main__":
    unittest.main()
