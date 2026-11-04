"""
Unit tests for full 8x8 Chess Game Module.
"""
import unittest
from games import chess_game


class TestChessGame(unittest.TestCase):
    def setUp(self):
        self.sessions = [{"id": 0, "name": "WhitePlayer"}, {"id": 1, "name": "BlackPlayer"}]
        self.state = chess_game.create_state(self.sessions)

    def test_initial_board_setup(self):
        board = self.state["board"]
        # Rank 8 has black pieces
        self.assertEqual(board[0][0], "r")
        self.assertEqual(board[0][4], "k")
        # Rank 1 has white pieces
        self.assertEqual(board[7][0], "R")
        self.assertEqual(board[7][4], "K")
        # Middle ranks are empty
        self.assertIsNone(board[3][3])
        self.assertEqual(chess_game.current_player(self.state), 0)

    def test_pawn_opening_move(self):
        # White plays e2e4 (row 6 col 4 to row 4 col 4)
        valid, act = chess_game.parse_action(self.state, 0, "e2e4")
        self.assertTrue(valid)
        self.assertEqual(act["notation"], "e2e4")

        events = chess_game.apply_action(self.state, 0, act)
        self.assertIn("log", events)
        # Verify piece moved
        self.assertIsNone(self.state["board"][6][4])
        self.assertEqual(self.state["board"][4][4], "P")
        # Now Black's turn
        self.assertEqual(chess_game.current_player(self.state), 1)

    def test_knight_movement(self):
        # White moves knight g1 to f3 (row 7 col 6 to row 5 col 5)
        valid, act = chess_game.parse_action(self.state, 0, "g1f3")
        self.assertTrue(valid)
        chess_game.apply_action(self.state, 0, act)
        self.assertEqual(self.state["board"][5][5], "N")
        self.assertIsNone(self.state["board"][7][6])

    def test_blocked_path_validation(self):
        # White bishop on c1 cannot move to a3 while pawn on b2 blocks it
        valid, err = chess_game.parse_action(self.state, 0, "c1a3")
        self.assertFalse(valid)

    def test_check_detection(self):
        # Clear path for black queen to check white king
        self.state["board"] = [[None] * 8 for _ in range(8)]
        self.state["board"][7][4] = "K"  # White King on e1
        self.state["board"][3][4] = "q"  # Black Queen on e5
        self.assertTrue(chess_game.is_king_in_check(self.state["board"], is_white=True))

    def test_enhanced_chess_rendering_clarity(self):
        # Verify Bishop and Soldier/Pawn have distinct, clear labels
        self.assertIn("B", chess_game.WHITE_COINS["B"])
        self.assertIn("P", chess_game.WHITE_COINS["P"])
        self.assertIn("b", chess_game.BLACK_COINS["b"])
        self.assertIn("p", chess_game.BLACK_COINS["p"])
        self.assertNotEqual(chess_game.WHITE_COINS["B"], chess_game.WHITE_COINS["P"])
        self.assertNotEqual(chess_game.BLACK_COINS["b"], chess_game.BLACK_COINS["p"])

        # Verify board and dashboard include piece guide
        view = chess_game.view_for(self.state, 0)
        dash = chess_game.render_dashboard(view)
        self.assertIn("COIN GUIDE", dash)
        self.assertIn("Bishop (B)", dash)
        self.assertIn("Soldier/Pawn (P)", dash)


if __name__ == "__main__":
    unittest.main()
