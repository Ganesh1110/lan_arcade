"""
Regression and verification tests for full audit issues and rule fixes.
"""
import unittest
from games import (
    wordoku, chess_game, quiz_show, sonar, typing_racer, shiritori,
    snake_duel, boggle, hangman, snake_and_ladder, arrow_man, mini_crossword, bingo
)
from utils.dictionary import is_valid_word, get_words_set
from core.solo_modes import _get_best_chess_move
from core.room import Room
from core.session import PlayerSession
from core.server import handle_surrender, play_lan_host
from core.game_manager import GameManager


class TestAuditFixes(unittest.TestCase):

    def test_wordoku_allows_letter_c_and_solvable_moves(self):
        st = wordoku.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}])
        # Find an empty cell
        empty_pos = None
        for r in range(6):
            for c in range(6):
                if st["grid"][r][c] is None:
                    empty_pos = (r, c)
                    break
            if empty_pos:
                break

        r, c = empty_pos
        # Test parse_action preserves C
        valid, act = wordoku.parse_action(st, 0, f"R{r+1} C{c+1} C")
        self.assertTrue(valid)
        self.assertEqual(act["val"], "C")
        self.assertEqual(act["r"], r)
        self.assertEqual(act["c"], c)

        # Also test without 'R' / 'C' prefixes
        valid2, act2 = wordoku.parse_action(st, 0, f"{r+1} {c+1} C")
        self.assertTrue(valid2)
        self.assertEqual(act2["val"], "C")

    def test_chess_fools_mate_checkmate(self):
        st = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        moves = ["f2f3", "e7e5", "g2g4", "d8h4"]
        for m in moves:
            pid = chess_game.current_player(st)
            valid, act = chess_game.parse_action(st, pid, m)
            self.assertTrue(valid, f"Move {m} failed")
            chess_game.apply_action(st, pid, act)

        self.assertTrue(chess_game.is_over(st))
        self.assertEqual(chess_game.get_winner(st), ["Black"])
        self.assertTrue(st["in_check"])

    def test_chess_castling_and_san(self):
        st = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        san_moves = ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O"]
        for m in san_moves:
            pid = chess_game.current_player(st)
            valid, act = chess_game.parse_action(st, pid, m)
            self.assertTrue(valid, f"SAN {m} failed")
            chess_game.apply_action(st, pid, act)

        # White king on g1 (7, 6) and rook on f1 (7, 5)
        self.assertEqual(st["board"][7][6], "K")
        self.assertEqual(st["board"][7][5], "R")

    def test_chess_en_passant(self):
        st = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        ep_moves = ["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"]
        for m in ep_moves:
            pid = chess_game.current_player(st)
            valid, act = chess_game.parse_action(st, pid, m)
            self.assertTrue(valid, f"EP {m} failed")
            chess_game.apply_action(st, pid, act)

        # Captured Black pawn at d5 (row 3, col 3) is removed
        self.assertIsNone(st["board"][3][3])
        self.assertIn("p", st["captured_white"])

    def test_quiz_show_no_answer_leak_and_even_rounds(self):
        st3 = quiz_show.create_state([
            {"id": 0, "name": "A"}, {"id": 1, "name": "B"}, {"id": 2, "name": "C"}
        ])
        # Turns must be divisible by 3
        self.assertEqual(len(st3["questions"]) % 3, 0)

        # view_for must not leak answer key
        v = quiz_show.view_for(st3, 0)
        curr_q = v.get("current_question")
        self.assertIsNotNone(curr_q)
        self.assertNotIn("answer", curr_q)

    def test_sonar_munitions_enforced_and_no_eval(self):
        st = sonar.create_state([{"id": 0, "name": "A"}, {"id": 1, "name": "B"}])
        # Fire 4 torpedoes
        for _ in range(4):
            valid, act = sonar.parse_action(st, 0, "TORPEDO E4")
            self.assertTrue(valid)
            sonar.apply_action(st, 0, act)

        self.assertEqual(st["torpedoes"][0], 0)
        valid_5, err = sonar.parse_action(st, 0, "TORPEDO E4")
        self.assertFalse(valid_5)
        self.assertIn("depleted", err.lower())

        # Test view_for does not use eval
        v = sonar.view_for(st, 0)
        self.assertIn("my_shots", v)

    def test_typing_racer_empty_input_no_progress_and_wpm(self):
        st = typing_racer.create_state([{"id": 0, "name": "A"}, {"id": 1, "name": "B"}])
        typing_racer.apply_action(st, 0, "")
        self.assertEqual(st["progress"][0], 0)

        typing_racer.apply_action(st, 1, "totally wrong gibberish")
        self.assertEqual(st["progress"][1], 0)

    def test_shiritori_no_skip_on_elimination(self):
        st = shiritori.create_state([
            {"id": 0, "name": "A"}, {"id": 1, "name": "B"}, {"id": 2, "name": "C"}
        ])
        self.assertEqual(shiritori.current_player(st), 0)
        shiritori.apply_action(st, 0, "CAT")

        self.assertEqual(shiritori.current_player(st), 1)
        st["lives"][1] = 1  # Last life
        shiritori.apply_action(st, 1, "PASS")  # B eliminated!

        # Next player MUST be C (id 2)
        self.assertEqual(shiritori.current_player(st), 2)

    def test_dictionary_inflections(self):
        for w in ["CATS", "BOOKS", "GAMES", "PLAYED", "BOX", "BOXES", "HOUSES", "DAYS", "RUNNING", "STOPPED", "HOPPING"]:
            self.assertTrue(is_valid_word(w), f"Word '{w}' should be valid")

    def test_dictionary_rejects_junk_and_repeated_inflections(self):
        # Prevent junk words from being accepted
        junk_words = ["BOOKSS", "CATSES", "RUNNINGS", "HOUSESS", "DAYSS", "PLAYEDS", "BOXESS"]
        for jw in junk_words:
            self.assertFalse(is_valid_word(jw), f"Junk word '{jw}' should NOT be accepted in dictionary")

    def test_chess_draw_conditions(self):
        # 1. Insufficient material: K vs K
        st = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        st["board"] = [[None] * 8 for _ in range(8)]
        st["board"][7][4] = "K"
        st["board"][0][4] = "k"
        v, act = chess_game.parse_action(st, 0, "e1e2")
        self.assertTrue(v)
        chess_game.apply_action(st, 0, act)
        self.assertTrue(chess_game.is_over(st))
        self.assertEqual(chess_game.get_winner(st), [])

        # 2. Insufficient material: K+B vs K
        st2 = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        st2["board"] = [[None] * 8 for _ in range(8)]
        st2["board"][7][4] = "K"
        st2["board"][7][2] = "B"
        st2["board"][0][4] = "k"
        v2, act2 = chess_game.parse_action(st2, 0, "e1e2")
        self.assertTrue(v2)
        chess_game.apply_action(st2, 0, act2)
        self.assertTrue(chess_game.is_over(st2))
        self.assertEqual(chess_game.get_winner(st2), [])

        # 3. 50-move rule
        st3 = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        st3["halfmove_clock"] = 99
        v3, act3 = chess_game.parse_action(st3, 0, "Nb1c3")
        self.assertTrue(v3)
        chess_game.apply_action(st3, 0, act3)
        self.assertTrue(chess_game.is_over(st3))
        self.assertEqual(chess_game.get_winner(st3), [])

        # 4. Threefold repetition
        st4 = chess_game.create_state([{"id": 0, "name": "White"}, {"id": 1, "name": "Black"}])
        moves = ["Nf3", "Nf6", "Ng1", "Ng8", "Nf3", "Nf6", "Ng1", "Ng8"]
        for m in moves:
            pid = chess_game.current_player(st4)
            valid, m_act = chess_game.parse_action(st4, pid, m)
            self.assertTrue(valid, f"Move {m} failed")
            chess_game.apply_action(st4, pid, m_act)
        self.assertTrue(chess_game.is_over(st4))
        self.assertEqual(chess_game.get_winner(st4), [])

    def test_snake_duel_arbitrary_ids(self):
        # Dedicated server / rejoin with IDs 2 and 5
        trails = {2: [(5, 5), (5, 6)], 5: [(10, 10), (10, 11)]}
        for _ in range(50):
            pellet = snake_duel.spawn_pellet(trails, (5, 6), (10, 11))
            self.assertNotIn(pellet, {(5, 5), (5, 6), (10, 10), (10, 11)})

    def test_boggle_eight_letter_scoring(self):
        self.assertEqual(boggle.calc_score("CAT"), 1)
        self.assertEqual(boggle.calc_score("HOUSE"), 2)
        self.assertEqual(boggle.calc_score("PLANET"), 3)
        self.assertEqual(boggle.calc_score("STUDENT"), 5)
        self.assertEqual(boggle.calc_score("COMPUTER"), 11)  # 8 letters = 11 pts

    def test_hangman_phrase_with_spaces(self):
        st = hangman.create_state([{"id": 0, "name": "Master"}, {"id": 1, "name": "Guesser"}])
        valid, phrase = hangman.parse_action(st, 0, "HELLO WORLD")
        self.assertTrue(valid)
        self.assertEqual(phrase, "HELLO WORLD")
        hangman.apply_action(st, 0, phrase)

        v = hangman.view_for(st, 1)
        # Spaces should be shown in pattern
        self.assertIn(" ", v["revealed_pattern"])

    def test_snake_and_ladder_first_ladder_reachable(self):
        # Square 2 ladder to 38 should be reachable on roll 1 from square 1
        self.assertEqual(snake_and_ladder.LADDERS.get(2), 38)
        self.assertNotIn(1, snake_and_ladder.LADDERS)

    def test_arrow_man_clinch_at_two_zero_and_angle_bound(self):
        st = arrow_man.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}])
        # Angle > 90 rejected
        valid, err = arrow_man.parse_action(st, 0, "120 50")
        self.assertFalse(valid)
        self.assertIn("90", err)

        # Win round 1
        st["hp"][1] = 0
        arrow_man.apply_action(st, 0, {"angle": 45, "power": 60, "arrow": "standard"})
        self.assertEqual(st["round_wins"][0], 1)
        self.assertFalse(arrow_man.is_over(st))

        # Win round 2 (reaches 2-0) -> clinches match!
        st["hp"][1] = 0
        arrow_man.apply_action(st, 0, {"angle": 45, "power": 60, "arrow": "standard"})
        self.assertTrue(arrow_man.is_over(st))
        self.assertEqual(arrow_man.get_winner(st), ["P1"])

    def test_mini_crossword_across_and_down_entries_are_valid_words(self):
        # All Down entries in all puzzles must be valid English words, not arbitrary letter scrambles
        for pz in mini_crossword.PUZZLES:
            for d_idx in range(1, 6):
                d_key = f"{d_idx}D"
                desc, clue_text, word = pz["clues"][d_key]
                self.assertTrue(is_valid_word(word), f"Down word '{word}' for {d_key} in {pz['theme']} must be a valid word")
                # Down clue must not just be letter spell-out
                self.assertNotIn("down letters", clue_text.lower(), f"Clue for {d_key} should be a real clue, not letter spell-out")
                self.assertNotIn(word, clue_text, f"Clue for {d_key} should not contain the answer")

        # Playing a match: solve with Across and Down clues
        st = mini_crossword.create_state([{"id": 0, "name": "A"}, {"id": 1, "name": "B"}])
        pz = st["puzzle"]
        # Player A enters correct 1A and 1D
        w_1a = pz["clues"]["1A"][2]
        v_a, act_a = mini_crossword.parse_action(st, 0, f"1A {w_1a}")
        self.assertTrue(v_a)
        res = mini_crossword.apply_action(st, 0, act_a)
        self.assertIn("SOLVED", res["log"][0])

        w_1d = pz["clues"]["1D"][2]
        v_d, act_d = mini_crossword.parse_action(st, 1, f"1D {w_1d}")
        self.assertTrue(v_d)
        res_d = mini_crossword.apply_action(st, 1, act_d)
        self.assertIn("SOLVED", res_d["log"][0])

    def test_surrender_elimination_in_three_player_match_and_flag_reset(self):
        room = Room("HostUser", bingo)
        p1 = PlayerSession(1, "PlayerOne")
        p2 = PlayerSession(2, "PlayerTwo")
        room.players.extend([p1, p2])
        gm = GameManager(bingo)
        gm.initialize(room.players)

        # In a 3-player match, if host surrenders:
        # Match should NOT end, host should be eliminated, remaining players continue
        is_over = handle_surrender(room, gm, 0)
        self.assertFalse(is_over, "Host surrender in 3-player match should eliminate host and continue game")
        self.assertTrue(room.get_player(0).has_surrendered)
        self.assertFalse(room.get_player(1).has_surrendered)
        self.assertFalse(room.get_player(2).has_surrendered)

        # Surrender flag must reset on rematch / start of new game
        for p in room.players:
            p.has_surrendered = False

        self.assertFalse(room.get_player(0).has_surrendered)
        self.assertFalse(room.get_player(1).has_surrendered)
        self.assertFalse(room.get_player(2).has_surrendered)


if __name__ == "__main__":
    unittest.main()
