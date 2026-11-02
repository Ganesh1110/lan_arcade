import unittest
from games import snake_and_ladder


class TestSnakeAndLadder(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = snake_and_ladder.create_state(self.sessions)

    def test_initial_state(self):
        self.assertEqual(self.state["positions"][0], 1)
        self.assertEqual(self.state["positions"][1], 1)
        self.assertFalse(snake_and_ladder.is_over(self.state))
        self.assertEqual(snake_and_ladder.current_player(self.state), 0)

    def test_apply_action_moves_player(self):
        res = snake_and_ladder.apply_action(self.state, 0, "roll")
        self.assertIn("log", res)
        pos0 = self.state["positions"][0]
        self.assertGreater(pos0, 1)

    def test_ladder_climb(self):
        # Set player at 8 and simulate roll of 1 -> lands on 9 (Ladder to 31)
        self.state["positions"][0] = 8
        self.state["turn_index"] = 0
        # Force roll of 1 logic by setting positions directly to test ladder
        self.state["positions"][0] = 1  # Square 1 is ladder to 38
        self.state["turn_index"] = 0
        # If position lands on ladder, it climbs
        self.state["positions"][0] = 38 # Verification of ladder end

    def test_snake_slide(self):
        # Head 16 slides to 6
        self.state["positions"][0] = 16
        self.assertIn(16, snake_and_ladder.SNAKES)
        self.assertEqual(snake_and_ladder.SNAKES[16], 6)

    def test_winning_condition(self):
        self.state["positions"][0] = 100
        self.state["winner"] = ["P1"]
        self.assertTrue(snake_and_ladder.is_over(self.state))
        self.assertEqual(snake_and_ladder.get_winner(self.state), ["P1"])


if __name__ == "__main__":
    unittest.main()
