import unittest
from games import (
    bingo, connect4, liars_dice, battleship,
    uno, dots_and_boxes, tic_tac_toe, mastermind
)

ALL_GAMES = [
    bingo, connect4, liars_dice, battleship,
    uno, dots_and_boxes, tic_tac_toe, mastermind
]


class TestAllGamesContract(unittest.TestCase):
    def test_game_modules_interface(self):
        for g in ALL_GAMES:
            sessions = [{"id": 0, "name": "HostPlayer"}, {"id": 1, "name": "GuestPlayer"}]
            state = g.create_state(sessions)
            self.assertIsNotNone(state)

            curr_pid = g.current_player(state)
            self.assertIn(curr_pid, [0, 1])

            view0 = g.view_for(state, 0)
            view1 = g.view_for(state, 1)
            self.assertIsNotNone(view0)
            self.assertIsNotNone(view1)

            prompt0 = g.prompt_for(view0, 0)
            self.assertIsInstance(prompt0, str)

            prompt_state0 = g.prompt_for(state, 0)
            self.assertIsInstance(prompt_state0, str)

            # Test dashboard and final rendering
            dash = g.render_dashboard(view0)
            self.assertIsInstance(dash, str)

            final = g.render_final(view0, "Test Game Over", ["HostPlayer"])
            self.assertIsInstance(final, str)

            # Test moves / actions
            raw_input = None
            if g == bingo:
                raw_input = "12"
            elif g == connect4:
                raw_input = "3"
            elif g == liars_dice:
                raw_input = "2 3"
            elif g == battleship:
                raw_input = "A1"
            elif g == uno:
                raw_input = "D"
            elif g == dots_and_boxes:
                raw_input = "H 1 1"
            elif g == tic_tac_toe:
                raw_input = "5"
            elif g == mastermind:
                raw_input = "1 2 3 4"

            # Parse action on state
            valid_st, act_st = g.parse_action(state, curr_pid, raw_input)
            self.assertTrue(valid_st, f"Game {g.game_name} failed parse_action on state with input '{raw_input}': {act_st}")

            # Parse action on view
            valid_v, act_v = g.parse_action(view0 if curr_pid == 0 else view1, curr_pid, raw_input)
            self.assertTrue(valid_v, f"Game {g.game_name} failed parse_action on view with input '{raw_input}': {act_v}")

            # Apply action
            events = g.apply_action(state, curr_pid, act_st)
            self.assertIsInstance(events, dict)
            self.assertIn("log", events)

            # Check is_over & get_winner
            self.assertIsInstance(g.is_over(state), bool)
            self.assertIsInstance(g.get_winner(state), list)


if __name__ == "__main__":
    unittest.main()
