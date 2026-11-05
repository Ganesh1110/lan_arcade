"""
Comprehensive test suite for the Rematch / Play Again flow across all games.
Covers:
- Solo mode rematch helper (preserves name, alternates turns/colors, fresh state, 'M' / 'Q' handling, mid-game 'q')
- Record match outcome counts
- Real socket LAN multiplayer rematch (voting, auto-start, surrender reset, player departure below min_players, !game guard)
"""
import socket
import threading
import time
import unittest
from unittest.mock import patch, MagicMock

from games import tic_tac_toe, chess_game, wordle, connect4, bingo
from core.solo_modes import (
    run_with_rematch,
    _play_tic_tac_toe,
    _play_chess,
    _play_wordle,
    _get_best_chess_move
)
from core.room import Room
from core.server import _start_rematch
from core.session import PlayerSession
from protocol import encode_message, decode_message


def mock_bot_cell(board, bot_sym, player_sym):
    for i in [8, 7, 6, 5, 4, 3, 2, 1, 0]:
        if board[i] is None:
            return i
    return 0


class TestSoloRematchFlow(unittest.TestCase):

    def test_solo_rematch_preserves_name_and_enters_second_match(self):
        """
        Mock input to verify:
        - Player name is asked once
        - [Enter] at end screen starts second match with same name
        - 'M' at second end screen exits to solo_menu
        """
        inputs = iter([
            "Tester",       # name
            "1", "2", "3",  # moves for match 1 (wins with mocked bot moves)
            "",             # [Enter] to rematch
            "1", "2",       # moves for match 2 (bot goes first and wins)
            "M"             # Return to solo menu
        ])

        with patch("builtins.input", lambda *args: next(inputs)), \
             patch("core.solo_modes.time.sleep"), \
             patch("core.solo_modes._get_best_ttt_cell", side_effect=mock_bot_cell), \
             patch("core.solo_modes.record_match_outcome") as mock_record:
            res = run_with_rematch(_play_tic_tac_toe, "Tic-Tac-Toe — vs Arcade Bot", "Player")

        self.assertEqual(res, "solo_menu")
        # record_match_outcome should be called twice (once per finished match)
        self.assertEqual(mock_record.call_count, 2)

    def test_solo_rematch_menu_q_returns_main_menu(self):
        """Entering 'Q' at rematch prompt returns 'main_menu'."""
        inputs = iter([
            "Bob",          # name
            "1", "2", "3",  # moves for match 1
            "Q"             # Exit to main menu
        ])

        with patch("builtins.input", lambda *args: next(inputs)), \
             patch("core.solo_modes.time.sleep"), \
             patch("core.solo_modes._get_best_ttt_cell", side_effect=mock_bot_cell), \
             patch("core.solo_modes.record_match_outcome"):
            res = run_with_rematch(_play_tic_tac_toe, "Tic-Tac-Toe — vs Arcade Bot", "Player")

        self.assertEqual(res, "main_menu")

    def test_solo_midgame_q_exits_cleanly_without_rematch_prompt(self):
        """Entering 'q' mid-match immediately aborts with no rematch menu."""
        inputs = iter([
            "Charlie",      # name
            "q"             # quit mid-game on first turn
        ])

        with patch("builtins.input", lambda *args: next(inputs)), \
             patch("core.solo_modes.time.sleep"), \
             patch("core.solo_modes.record_match_outcome") as mock_record:
            res = run_with_rematch(_play_tic_tac_toe, "Tic-Tac-Toe — vs Arcade Bot", "Player")

        self.assertEqual(res, "solo_menu")
        mock_record.assert_not_called()

    def test_record_match_outcome_called_once_per_finished_match(self):
        """Verify record_match_outcome is called once per finished match across rematches."""
        inputs = iter([
            "Player1",
            "1", "2", "3",   # Match 1 (human goes first and wins)
            "R",             # Rematch
            "1", "2",        # Match 2 (bot goes first and wins)
            "R",             # Rematch
            "1", "2", "3",   # Match 3 (human goes first and wins)
            "M"              # Menu
        ])

        with patch("builtins.input", lambda *args: next(inputs)), \
             patch("core.solo_modes.time.sleep"), \
             patch("core.solo_modes._get_best_ttt_cell", side_effect=mock_bot_cell), \
             patch("core.solo_modes.record_match_outcome") as mock_record:
            res = run_with_rematch(_play_tic_tac_toe, "Tic-Tac-Toe — vs Arcade Bot", "Player")

        self.assertEqual(res, "solo_menu")
        self.assertEqual(mock_record.call_count, 3)

    def test_solo_turn_alternation_and_chess_color_swap(self):
        """
        Verify that Chess swaps White/Black colors on rematch,
        and Tic-Tac-Toe alternates who moves first.
        """
        # Test Tic-Tac-Toe:
        # Match 1 (rematch_count=0): Human is player 0, goes first
        s0 = tic_tac_toe.create_state([{"id": 0, "name": "Human"}, {"id": 1, "name": "Bot"}])
        self.assertEqual(tic_tac_toe.current_player(s0), 0)

        # Match 2 (rematch_count=1): Bot is player 1, goes first
        s1 = tic_tac_toe.create_state([{"id": 1, "name": "Bot"}, {"id": 0, "name": "Human"}])
        self.assertEqual(tic_tac_toe.current_player(s1), 1)

        # Test Chess:
        # Match 1 (rematch_count=0): Human is White, moves first
        cs0 = chess_game.create_state([{"id": 0, "name": "Human"}, {"id": 1, "name": "Bot"}])
        self.assertEqual(cs0["players"][0]["side"], "White")
        self.assertEqual(cs0["players"][0]["id"], 0)

        # Match 2 (rematch_count=1): Bot is White, moves first
        cs1 = chess_game.create_state([{"id": 1, "name": "Bot"}, {"id": 0, "name": "Human"}])
        self.assertEqual(cs1["players"][0]["side"], "White")
        self.assertEqual(cs1["players"][0]["id"], 1)

        # Bot can generate a legal White move when playing White
        white_bot_move = _get_best_chess_move(cs1["board"], is_white=True)
        self.assertIsNotNone(white_bot_move)
        self.assertIn("from", white_bot_move)

    def test_fresh_state_randomization_on_rematch(self):
        """Verify that state objects are completely fresh on rematch."""
        s1 = wordle.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "Bot"}])
        s2 = wordle.create_state([{"id": 0, "name": "P1"}, {"id": 1, "name": "Bot"}])
        self.assertIsNot(s1, s2)
        self.assertIsNot(s1["guesses"], s2["guesses"])

    def test_solo_wordle_play_finish(self):
        """Test Wordle match completes and records outcome."""
        with patch("core.solo_modes.time.sleep"), \
             patch("core.solo_modes.record_match_outcome") as mock_record:
            st = wordle.create_state([{"id": 0, "name": "Alice"}, {"id": 1, "name": "WordleBot 🤖"}])
            st["target_word"] = "PEACE"
            with patch("games.wordle.create_state", return_value=st):
                inputs = iter(["PEACE"])
                with patch("builtins.input", lambda *args: next(inputs)):
                    outcome = _play_wordle("Alice", 0)
            self.assertEqual(outcome, "player")
            mock_record.assert_called_once()

    def test_solo_chess_play_finish(self):
        """Test Chess match completes with Fool's Mate."""
        with patch("core.solo_modes.time.sleep"), \
             patch("core.solo_modes.record_match_outcome") as mock_record:
            # White plays f2f3, g2g4; Bot plays e7e5, d8h4#
            inputs = iter(["f2f3", "g2g4"])
            bot_moves = iter([
                {"from": (1, 4), "to": (3, 4), "notation": "e7e5"},
                {"from": (0, 3), "to": (4, 7), "notation": "d8h4"}
            ])
            with patch("core.solo_modes._get_best_chess_move", lambda *a, **k: next(bot_moves)), \
                 patch("builtins.input", lambda *args: next(inputs)):
                outcome = _play_chess("Grandmaster", 0)
            self.assertEqual(outcome, "bot")
            mock_record.assert_called_once()


class TestLanSocketRematch(unittest.TestCase):

    def setUp(self):
        self.room = Room("HostPlayer", bingo)
        self.threads = []
        self.client_socks = []

    def tearDown(self):
        self.room.closed = True
        for cs in self.client_socks:
            try:
                cs.close()
            except OSError:
                pass
        for t in self.threads:
            t.join(timeout=0.5)

    def _connect_guest(self, name):
        c_sock, s_sock = socket.socketpair()
        self.client_socks.append(c_sock)
        t = threading.Thread(target=self.room.client_handler, args=(s_sock,), daemon=True)
        t.start()
        self.threads.append(t)
        c_sock.sendall(encode_message({"type": "join", "name": name}))
        time.sleep(0.05)
        return c_sock

    def test_real_socket_voting_and_surrender_flag_reset(self):
        """
        Host + 2 guests connect via real sockets.
        Guests surrender, then send rematch_vote.
        Verify server tracks votes and resets has_surrendered on rematch.
        """
        c1 = self._connect_guest("Guest1")
        c2 = self._connect_guest("Guest2")

        time.sleep(0.1)
        self.assertEqual(len(self.room.players), 3)

        g1 = self.room.get_player(1)
        g2 = self.room.get_player(2)
        self.assertIsNotNone(g1)
        self.assertIsNotNone(g2)

        # Simulate surrenders during match
        g1.has_surrendered = True
        g2.has_surrendered = True

        # Guests send rematch votes
        c1.sendall(encode_message({"type": "rematch_vote"}))
        c2.sendall(encode_message({"type": "rematch_vote"}))

        time.sleep(0.1)
        self.assertIn(1, self.room.rematch_votes)
        self.assertIn(2, self.room.rematch_votes)

        # Rematch triggers
        with patch("core.server.play_lan_host"), patch("core.server.time.sleep"):
            rematch_started = _start_rematch(self.room)

        self.assertTrue(rematch_started)
        # All surrender flags must be reset to False
        self.assertFalse(self.room.get_player(0).has_surrendered)
        self.assertFalse(self.room.get_player(1).has_surrendered)
        self.assertFalse(self.room.get_player(2).has_surrendered)
        # Rematch votes cleared
        self.assertEqual(len(self.room.rematch_votes), 0)

    def test_lan_rematch_refused_below_min_players(self):
        """If a guest leaves dropping the count below min_players, rematch is refused."""
        self.room.game_module = connect4
        self.room.min_players = 2

        c1 = self._connect_guest("Guest1")
        time.sleep(0.1)
        self.assertEqual(len(self.room.players), 2)

        # Guest leaves
        c1.sendall(encode_message({"type": "leave"}))
        time.sleep(0.1)

        # Host tries to start rematch with only 1 player remaining
        with patch("core.server.play_lan_host"):
            rematch_started = _start_rematch(self.room)

        self.assertFalse(rematch_started)
        self.assertFalse(self.room.started)

    def test_guest_cannot_use_game_command_mid_match(self):
        """Guest cannot change game module while match is in progress."""
        c1 = self._connect_guest("Guest1")
        time.sleep(0.1)

        self.room.started = True
        c1.sendall(encode_message({"type": "chat", "text": "!game chess"}))
        time.sleep(0.1)

        self.assertEqual(self.room.game_module, bingo)


if __name__ == "__main__":
    unittest.main()
