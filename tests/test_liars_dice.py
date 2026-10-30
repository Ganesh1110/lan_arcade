import unittest
from games import liars_dice


class TestLiarsDice(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = liars_dice.create_state(sessions)

    def test_privacy_view(self):
        v0 = liars_dice.view_for(self.state, 0)
        v1 = liars_dice.view_for(self.state, 1)

        # Ensure P0 only receives P0's dice
        self.assertEqual(len(v0["own_dice"]), 5)
        # Ensure view does not expose P1's dice array
        self.assertNotIn("dice", v0)

    def test_bid_and_challenge(self):
        # P1 bids 2 threes
        valid, act = liars_dice.parse_action(self.state, 0, "2 3")
        self.assertTrue(valid)
        liars_dice.apply_action(self.state, 0, act)

        # P2 challenges
        valid, act2 = liars_dice.parse_action(self.state, 1, "C")
        self.assertTrue(valid)
        res = liars_dice.apply_action(self.state, 1, act2)

        self.assertIsNotNone(self.state["last_challenge_result"])


if __name__ == "__main__":
    unittest.main()
