import unittest
from games import (
    bingo, connect4, battleship,
    dots_and_boxes, tic_tac_toe, hangman,
    shiritori, game2048,
    boggle, mini_crossword, wordoku, scrabble_sprint, snake_and_ladder,
    chess_game, wordle, quiz_show, typing_racer,
    artillery, snake_duel, sonar, arrow_man, memory_match
)

ALL_GAMES = [
    bingo, connect4, battleship,
    dots_and_boxes, tic_tac_toe, hangman,
    shiritori, game2048,
    boggle, mini_crossword, wordoku, scrabble_sprint, snake_and_ladder,
    chess_game, wordle, quiz_show, typing_racer,
    artillery, snake_duel, sonar, arrow_man, memory_match
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
            elif g == battleship:
                raw_input = "A1"
            elif g == dots_and_boxes:
                raw_input = "H 1 1"
            elif g == tic_tac_toe:
                raw_input = "5"
            elif g == hangman:
                raw_input = "COMPUTER"
            elif g == shiritori:
                raw_input = "APPLE"
            elif g == game2048:
                raw_input = "W"
            elif g == boggle:
                raw_input = "pass"
            elif g == mini_crossword:
                raw_input = "1A APPLE"
            elif g == wordoku:
                empty_r, empty_c = 1, 1
                for r_idx in range(6):
                    for c_idx in range(6):
                        if state["grid"][r_idx][c_idx] is None:
                            empty_r, empty_c = r_idx + 1, c_idx + 1
                            break
                    if state["grid"][empty_r - 1][empty_c - 1] is None:
                        break
                raw_input = f"R{empty_r} C{empty_c} A"
            elif g == scrabble_sprint:
                raw_input = "pass"
            elif g == snake_and_ladder:
                raw_input = "r"
            elif g == chess_game:
                raw_input = "e2e4"
            elif g == wordle:
                raw_input = "CRANE"
            elif g == quiz_show:
                raw_input = "B"
            elif g == typing_racer:
                raw_input = "test"
            elif g == artillery:
                raw_input = "45 60"
            elif g == snake_duel:
                raw_input = "W"
            elif g == sonar:
                raw_input = "MOVE N"
            elif g == arrow_man:
                raw_input = "45 70"
            elif g == memory_match:
                raw_input = "A1 A2"

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
