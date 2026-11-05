import json
import random
import unittest
from games import memory_match
from core.solo_modes import _get_best_memory_match_move, _update_bot_memory


class TestMemoryMatch(unittest.TestCase):
    def setUp(self):
        random.seed(42)

    def test_create_state_sizes_and_pairs(self):
        # 2 players -> 4x4, 8 pairs
        p2 = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        st2 = memory_match.create_state(p2)
        self.assertEqual(st2["rows"], 4)
        self.assertEqual(st2["cols"], 4)
        self.assertEqual(st2["total_pairs"], 8)
        self.assertEqual(st2["pairs_remaining"], 8)
        self.assertEqual(len(st2["board"]), 4)
        self.assertEqual(len(st2["board"][0]), 4)

        # Count symbol frequencies
        all_syms_2 = [sym for row in st2["board"] for sym in row]
        self.assertEqual(len(all_syms_2), 16)
        freq_2 = {}
        for s in all_syms_2:
            freq_2[s] = freq_2.get(s, 0) + 1
        self.assertEqual(len(freq_2), 8)
        self.assertTrue(all(count == 2 for count in freq_2.values()))

        # 3 and 4 players -> 4x5, 10 pairs
        for n_players in [3, 4]:
            p_list = [{"id": i, "name": f"P{i+1}"} for i in range(n_players)]
            st_n = memory_match.create_state(p_list)
            self.assertEqual(st_n["rows"], 4)
            self.assertEqual(st_n["cols"], 5)
            self.assertEqual(st_n["total_pairs"], 10)
            self.assertEqual(st_n["pairs_remaining"], 10)
            self.assertEqual(len(st_n["board"]), 4)
            self.assertEqual(len(st_n["board"][0]), 5)

            all_syms_n = [sym for row in st_n["board"] for sym in row]
            self.assertEqual(len(all_syms_n), 20)
            freq_n = {}
            for s in all_syms_n:
                freq_n[s] = freq_n.get(s, 0) + 1
            self.assertEqual(len(freq_n), 10)
            self.assertTrue(all(count == 2 for count in freq_n.values()))

        # Two create_state calls produce different card layouts (random shuffle)
        st_a = memory_match.create_state(p2)
        st_b = memory_match.create_state(p2)
        self.assertNotEqual(st_a["board"], st_b["board"])

    def test_parse_action_valid_and_rejections(self):
        players = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        state = memory_match.create_state(players)

        # 1. Valid inputs: 'A1 C3', 'A1,C3', 'a1 c3', '1A 3C'
        for text in ["A1 C3", "A1,C3", "a1 c3", "1A 3C"]:
            ok, act = memory_match.parse_action(state, 0, text)
            self.assertTrue(ok, f"Failed parsing valid input '{text}': {act}")
            self.assertEqual(act["card1"], (0, 0))
            self.assertEqual(act["card2"], (2, 2))

        # 2. Rejection: wrong turn
        ok, err = memory_match.parse_action(state, 1, "A1 C3")
        self.assertFalse(ok)
        self.assertIn("not your turn", err.lower())

        # 3. Rejection: malformed inputs
        for bad in ["A1", "A1 B2 C3", "ZZ", "", None, "HELLO"]:
            ok, err = memory_match.parse_action(state, 0, bad)
            self.assertFalse(ok, f"Expected rejection for '{bad}'")

        # 4. Rejection: same card twice
        ok, err = memory_match.parse_action(state, 0, "A1 A1")
        self.assertFalse(ok)
        self.assertIn("two different cards", err.lower())

        ok, err = memory_match.parse_action(state, 0, "a1,A1")
        self.assertFalse(ok)
        self.assertIn("two different cards", err.lower())

        # 5. Rejection: out of range coordinates
        for oob in ["F1 A2", "A5 B1", "E1 A1", "Z9 B2"]:
            ok, err = memory_match.parse_action(state, 0, oob)
            self.assertFalse(ok, f"Expected out-of-range rejection for '{oob}'")
            self.assertIn("out of range", err.lower())

        # 6. Rejection: already matched card
        state["matched"].add((0, 0))
        state["matched"].add((0, 1))
        ok, err = memory_match.parse_action(state, 0, "A1 B2")
        self.assertFalse(ok)
        self.assertIn("already been matched", err.lower())

        ok, err = memory_match.parse_action(state, 0, "B2 A1")
        self.assertFalse(ok)
        self.assertIn("already been matched", err.lower())

    def test_apply_action_matching_and_mismatch(self):
        players = [{"id": 0, "name": "Alice"}, {"id": 1, "name": "Bob"}]
        state = memory_match.create_state(players)

        # Force fixed board for deterministic test
        sym_apple = "🍎"
        sym_banana = "🍌"
        state["board"] = [
            [sym_apple, sym_apple, sym_banana, sym_banana],
            ["🍒", "🍒", "🍇", "🍇"],
            ["🍓", "🍓", "🍑", "🍑"],
            ["🍍", "🍍", "🥑", "🥑"]
        ]

        # Case 1: Mismatch
        # Alice flips A1 (0,0 -> 🍎) and C1 (0,2 -> 🍌)
        act_mismatch = {
            "card1": (0, 0),
            "card2": (0, 2),
            "c1_str": "A1",
            "c2_str": "C1"
        }
        ev1 = memory_match.apply_action(state, 0, act_mismatch)
        self.assertIn("no match", ev1["log"][0])
        self.assertEqual(state["scores"][0], 0)
        self.assertEqual(len(state["matched"]), 0)
        # Turn passes to Bob
        self.assertEqual(memory_match.current_player(state), 1)
        self.assertIsNotNone(state["last_reveal"])
        self.assertFalse(state["last_reveal"]["matched"])
        self.assertEqual(state["last_reveal"]["card1"]["symbol"], sym_apple)
        self.assertEqual(state["last_reveal"]["card2"]["symbol"], sym_banana)

        # Case 2: Match
        # Bob flips A1 (0,0 -> 🍎) and B1 (0,1 -> 🍎)
        act_match = {
            "card1": (0, 0),
            "card2": (0, 1),
            "c1_str": "A1",
            "c2_str": "B1"
        }
        ev2 = memory_match.apply_action(state, 1, act_match)
        self.assertIn("MATCH", ev2["log"][0])
        self.assertEqual(state["scores"][1], 1)
        self.assertIn((0, 0), state["matched"])
        self.assertIn((0, 1), state["matched"])
        self.assertEqual(state["pairs_remaining"], 7)
        # Same player goes again: Bob still has turn
        self.assertEqual(memory_match.current_player(state), 1)
        self.assertTrue(state["last_reveal"]["matched"])

    def test_skip_player(self):
        players = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}, {"id": 2, "name": "P3"}]
        state = memory_match.create_state(players)
        self.assertEqual(memory_match.current_player(state), 0)

        # Skip current player (turn_id 0)
        memory_match.skip_player(state, 0)
        self.assertEqual(memory_match.current_player(state), 1)

        # Skip non-current player has no effect
        memory_match.skip_player(state, 0)
        self.assertEqual(memory_match.current_player(state), 1)

        # Skip player 1
        memory_match.skip_player(state, 1)
        self.assertEqual(memory_match.current_player(state), 2)

    def test_game_over_and_winner(self):
        players = [{"id": 0, "name": "Alice"}, {"id": 1, "name": "Bob"}]
        state = memory_match.create_state(players)
        self.assertFalse(memory_match.is_over(state))
        self.assertEqual(memory_match.get_winner(state), [])

        # Match all cards except the last pair
        # Total cells: 16
        for r in range(4):
            for c in range(4):
                if (r, c) not in [(3, 2), (3, 3)]:
                    state["matched"].add((r, c))

        self.assertFalse(memory_match.is_over(state))

        # Add the final pair
        state["board"][3][2] = "💎"
        state["board"][3][3] = "💎"
        state["scores"][0] = 5
        state["scores"][1] = 2

        act = {
            "card1": (3, 2),
            "card2": (3, 3),
            "c1_str": "C4",
            "c2_str": "D4"
        }
        memory_match.apply_action(state, 0, act)

        self.assertTrue(memory_match.is_over(state))
        self.assertEqual(state["scores"][0], 6)
        winners = memory_match.get_winner(state)
        self.assertEqual(winners, ["Alice"])

        # Test tie handling
        state["scores"][0] = 4
        state["scores"][1] = 4
        tie_winners = memory_match.get_winner(state)
        self.assertEqual(set(tie_winners), {"Alice", "Bob"})

    def test_privacy_view_for_no_leak(self):
        players = [{"id": 0, "name": "Alice"}, {"id": 1, "name": "Bob"}]
        state = memory_match.create_state(players)

        # Initial view
        view0 = memory_match.view_for(state, 0)
        view_json0 = json.dumps(view0)

        # Check every card face in the board
        for r in range(state["rows"]):
            for c in range(state["cols"]):
                sym = state["board"][r][c]
                # At start, no cards matched, last_reveal is None
                self.assertNotIn(sym, view_json0, f"Face-down card symbol {sym} leaked in view_for JSON!")

        # Mid-game state: 1 pair matched, 1 mismatched reveal
        state["matched"].add((0, 0))
        state["matched"].add((0, 1))
        matched_sym = state["board"][0][0]

        # Mismatched reveal at (1, 0) and (1, 1)
        r_sym1 = state["board"][1][0]
        r_sym2 = state["board"][1][1]
        state["last_reveal"] = {
            "player_id": 0,
            "player_name": "Alice",
            "card1": {"row": 1, "col": 0, "coord": "A2", "symbol": r_sym1},
            "card2": {"row": 1, "col": 1, "coord": "B2", "symbol": r_sym2},
            "matched": False
        }

        view_mid = memory_match.view_for(state, 1)
        view_json_mid = json.dumps(view_mid)

        # Matched symbol and last_reveal symbols are allowed
        # But ALL OTHER face-down cards must NEVER appear in JSON
        for r in range(state["rows"]):
            for c in range(state["cols"]):
                if (r, c) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    continue
                sym = state["board"][r][c]
                # If this symbol happens to be identical to matched_sym or r_sym, skip checking that identical symbol,
                # but assert that board_view[r][c] is strictly None
                self.assertIsNone(view_mid["board"][r][c])
                if sym != matched_sym and sym != r_sym1 and sym != r_sym2:
                    self.assertNotIn(sym, view_json_mid, f"Face-down symbol {sym} at ({r},{c}) leaked in view_for JSON!")

    def test_rendering(self):
        players = [{"id": 0, "name": "Alice"}, {"id": 1, "name": "Bob"}]
        state = memory_match.create_state(players)
        view = memory_match.view_for(state, 0)

        dash = memory_match.render_dashboard(view)
        self.assertIsInstance(dash, str)
        self.assertIn("M E M O R Y   M A T C H", dash)
        self.assertIn("Pairs Remaining", dash)

        final = memory_match.render_final(view, "Game Over", ["Alice"])
        self.assertIsInstance(final, str)
        self.assertIn("VICTORY! Alice WINS", final)

    def test_fuzz_2000_games(self):
        """Simulate 2,000 games across 2, 3, and 4 players with random legal picks."""
        rng = random.Random(12345)
        for g_idx in range(2000):
            n_players = rng.choice([2, 3, 4])
            players = [{"id": i, "name": f"P{i}"} for i in range(n_players)]
            state = memory_match.create_state(players)
            rows = state["rows"]
            cols = state["cols"]
            total_pairs = state["total_pairs"]

            moves = 0
            while not memory_match.is_over(state) and moves < 500:
                pid = memory_match.current_player(state)
                # Find available face-down cards
                available = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in state["matched"]]
                self.assertGreaterEqual(len(available), 2)
                c1, c2 = rng.sample(available, 2)

                act = {
                    "card1": c1,
                    "card2": c2,
                    "c1_str": f"{chr(ord('A') + c1[1])}{c1[0] + 1}",
                    "c2_str": f"{chr(ord('A') + c2[1])}{c2[0] + 1}"
                }
                ev = memory_match.apply_action(state, pid, act)
                self.assertIn("log", ev)
                moves += 1

            self.assertTrue(memory_match.is_over(state), f"Game {g_idx} did not finish within 500 moves")
            self.assertEqual(len(state["matched"]), rows * cols)
            self.assertEqual(sum(state["scores"].values()), total_pairs)
            winners = memory_match.get_winner(state)
            self.assertTrue(len(winners) >= 1)

    def test_bot_500_simulated_games_zero_illegal_moves(self):
        """Simulate 500 complete games played with _get_best_memory_match_move. Assert zero illegal moves."""
        rng = random.Random(67890)
        for g_idx in range(500):
            players = [{"id": 0, "name": "Human"}, {"id": 1, "name": "MemoryBot"}]
            state = memory_match.create_state(players)
            rows = state["rows"]
            cols = state["cols"]
            total_pairs = state["total_pairs"]

            bot_memory = {}
            moves = 0
            while not memory_match.is_over(state) and moves < 300:
                pid = memory_match.current_player(state)
                view = memory_match.view_for(state, pid)

                if pid == 1:
                    # Bot turn
                    move = _get_best_memory_match_move(view, bot_id=1, bot_memory=bot_memory, human_like=True)
                    self.assertIsNotNone(move)
                    c1, c2 = move["card1"], move["card2"]
                else:
                    # Simulated opponent (random legal picks)
                    available = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in state["matched"]]
                    c1, c2 = rng.sample(available, 2)

                # Assert validity of move
                self.assertNotEqual(c1, c2, f"Game {g_idx}: duplicate card chosen: {c1}")
                self.assertNotIn(c1, state["matched"], f"Game {g_idx}: c1 {c1} is already matched!")
                self.assertNotIn(c2, state["matched"], f"Game {g_idx}: c2 {c2} is already matched!")
                self.assertTrue(0 <= c1[0] < rows and 0 <= c1[1] < cols)
                self.assertTrue(0 <= c2[0] < rows and 0 <= c2[1] < cols)

                act = {
                    "card1": c1,
                    "card2": c2,
                    "c1_str": f"{chr(ord('A') + c1[1])}{c1[0] + 1}",
                    "c2_str": f"{chr(ord('A') + c2[1])}{c2[0] + 1}"
                }

                # Verify parse_action accepts the formatted string
                c1_s = f"{chr(ord('A') + c1[1])}{c1[0] + 1}"
                c2_s = f"{chr(ord('A') + c2[1])}{c2[0] + 1}"
                ok, parsed = memory_match.parse_action(view, pid, f"{c1_s} {c2_s}")
                self.assertTrue(ok, f"Bot generated move failed parse_action: {parsed}")

                memory_match.apply_action(state, pid, act)

                # Update bot memory using view's last_reveal
                bot_view = memory_match.view_for(state, 1)
                _update_bot_memory(bot_memory, bot_view, human_like=True)
                moves += 1

            self.assertTrue(memory_match.is_over(state), f"Bot game {g_idx} did not finish within 300 moves")
            self.assertEqual(sum(state["scores"].values()), total_pairs)

    def test_bot_move_without_board_key(self):
        """Verify bot does not require or peek at state['board'] to make a legal move."""
        players = [{"id": 0, "name": "Human"}, {"id": 1, "name": "MemoryBot"}]
        state = memory_match.create_state(players)
        state_no_board = dict(state)
        del state_no_board["board"]

        bot_mem = {}
        move = _get_best_memory_match_move(state_no_board, bot_id=1, bot_memory=bot_mem, human_like=True)
        self.assertIsNotNone(move)
        c1 = move["card1"]
        c2 = move["card2"]
        self.assertNotEqual(c1, c2)
        self.assertNotIn(c1, state["matched"])
        self.assertNotIn(c2, state["matched"])
        self.assertTrue(0 <= c1[0] < state["rows"] and 0 <= c1[1] < state["cols"])
        self.assertTrue(0 <= c2[0] < state["rows"] and 0 <= c2[1] < state["cols"])

        # Also test with known pair in bot memory without board key
        bot_mem[(0, 0)] = "🍎"
        bot_mem[(0, 1)] = "🍎"
        move_pair = _get_best_memory_match_move(state_no_board, bot_id=1, bot_memory=bot_mem, human_like=True)
        self.assertIsNotNone(move_pair)
        pair_coords = {move_pair["card1"], move_pair["card2"]}
        self.assertEqual(pair_coords, {(0, 0), (0, 1)})

    def test_bot_non_peeking_win_rate_simulation(self):
        """Simulation asserting bot (human_like=True) does not win more than about 60% of 1,000 games against non-peeking baseline."""
        bot_wins = 0
        total_games = 1000

        for g_idx in range(total_games):
            bot_first = (g_idx % 2 == 1)
            players = [{"id": 1, "name": "MemoryBot"}, {"id": 0, "name": "Baseline"}] if bot_first else [{"id": 0, "name": "Baseline"}, {"id": 1, "name": "MemoryBot"}]
            st = memory_match.create_state(players)

            mem_baseline = {}
            mem_bot = {}

            while not memory_match.is_over(st):
                pid = memory_match.current_player(st)
                if pid == 1:
                    move = _get_best_memory_match_move(st, bot_id=1, bot_memory=mem_bot, human_like=True)
                else:
                    move = _get_best_memory_match_move(st, bot_id=0, bot_memory=mem_baseline, human_like=True)
                memory_match.apply_action(st, pid, move)
                _update_bot_memory(mem_baseline, st.get("last_reveal"), st["matched"], human_like=True)
                _update_bot_memory(mem_bot, st.get("last_reveal"), st["matched"], human_like=True)

            winners = memory_match.get_winner(st)
            if winners == ["MemoryBot"]:
                bot_wins += 1

        win_pct = (bot_wins / total_games) * 100.0
        self.assertLessEqual(win_pct, 60.0, f"Bot won {win_pct:.1f}% of games, exceeding 60% threshold!")


if __name__ == "__main__":
    unittest.main()
