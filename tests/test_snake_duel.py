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

    def test_fruit_eating_grows_snake_and_scores(self):
        # Place fruit directly in path of player 0
        self.state["positions"][0] = (5, 5)
        self.state["directions"][0] = (1, 0)
        self.state["pellet"] = (6, 5)
        old_len = self.state["lengths"][0]
        old_score = self.state["scores"][0]

        snake_duel.apply_action(self.state, 0, "D")
        self.assertEqual(self.state["positions"][0], (6, 5))
        self.assertEqual(self.state["scores"][0], old_score + snake_duel.POINTS_PER_FRUIT)
        self.assertEqual(self.state["lengths"][0], old_len + 1)
        self.assertTrue(self.state["alive"][0])

    def test_tail_trims_when_not_eating_fruit(self):
        # Move without fruit and ensure trail doesn't exceed snake length
        self.state["pellet"] = (25, 12)  # Far away
        self.state["positions"][0] = (5, 5)
        self.state["trails"][0] = [(5, 5)]
        self.state["lengths"][0] = 2

        snake_duel.apply_action(self.state, 0, "D")  # to (6, 5), len becomes 2
        self.assertEqual(len(self.state["trails"][0]), 2)

        snake_duel.apply_action(self.state, 0, "D")  # to (7, 5), len remains 2 (tail trimmed)
        self.assertEqual(len(self.state["trails"][0]), 2)
        self.assertEqual(self.state["trails"][0], [(6, 5), (7, 5)])

    def test_no_limit_endless_survival(self):
        # Fruit eating increases score and length with no forced limit/cap
        self.state["scores"][0] = 50
        self.state["lengths"][0] = 7
        self.state["positions"][0] = (5, 5)
        self.state["directions"][0] = (1, 0)
        self.state["pellet"] = (6, 5)

        snake_duel.apply_action(self.state, 0, "D")
        self.assertEqual(self.state["scores"][0], 60)
        self.assertEqual(self.state["lengths"][0], 8)
        self.assertTrue(self.state["alive"][0])
        # Game does NOT end on reaching 50 or 60 pts; it is endless survival until crash!
        self.assertFalse(snake_duel.is_over(self.state))


if __name__ == "__main__":
    unittest.main()
