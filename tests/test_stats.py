"""
Unit tests for Persistent Stats and Hall of Fame tracking.
"""
import os
import unittest
import utils.stats as stats_mod


class TestStats(unittest.TestCase):
    def setUp(self):
        # Point to a temporary stats file for isolation
        self.orig_stats_file = stats_mod._STATS_FILE
        self.test_stats_file = os.path.join(stats_mod._DATA_DIR, "test_stats_temp.json")
        stats_mod._STATS_FILE = self.test_stats_file
        if os.path.exists(self.test_stats_file):
            os.remove(self.test_stats_file)

    def tearDown(self):
        if os.path.exists(self.test_stats_file):
            os.remove(self.test_stats_file)
        stats_mod._STATS_FILE = self.orig_stats_file

    def test_record_match_outcome(self):
        stats_mod.record_match_outcome("Connect Four", ["Alice", "Bob"], ["Alice"])
        data = stats_mod._load_data()
        self.assertIn("Alice", data["players"])
        self.assertIn("Bob", data["players"])
        self.assertEqual(data["players"]["Alice"]["wins"], 1)
        self.assertEqual(data["players"]["Alice"]["losses"], 0)
        self.assertEqual(data["players"]["Alice"]["streak"], 1)
        self.assertEqual(data["players"]["Bob"]["wins"], 0)
        self.assertEqual(data["players"]["Bob"]["losses"], 1)
        self.assertEqual(data["players"]["Bob"]["streak"], 0)

    def test_record_high_score(self):
        stats_mod.record_high_score("game2048", "Champion", 4096, "Tile: 512")
        stats_mod.record_high_score("game2048", "RunnerUp", 2048, "Tile: 256")
        data = stats_mod._load_data()
        self.assertIn("game2048", data["high_scores"])
        scores = data["high_scores"]["game2048"]
        self.assertEqual(scores[0]["player"], "Champion")
        self.assertEqual(scores[0]["score"], 4096)
        self.assertEqual(scores[1]["player"], "RunnerUp")
        self.assertEqual(scores[1]["score"], 2048)

    def test_render_hall_of_fame(self):
        stats_mod.record_match_outcome("Tic-Tac-Toe", ["P1", "P2"], ["P1"])
        stats_mod.record_high_score("boggle", "WordMaster", 42)
        hof_output = stats_mod.render_hall_of_fame()
        self.assertIsInstance(hof_output, str)
        self.assertIn("H A L L   O F   F A M E", hof_output)
        self.assertIn("P1", hof_output)
        self.assertIn("WordMaster", hof_output)


if __name__ == "__main__":
    unittest.main()
