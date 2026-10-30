import unittest
from games import uno


class TestUno(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = uno.create_state(sessions)

    def test_privacy_hand(self):
        v0 = uno.view_for(self.state, 0)
        self.assertEqual(len(v0["own_hand"]), 7)
        self.assertNotIn("hands", v0)

    def test_draw_card(self):
        v0 = uno.view_for(self.state, 0)
        valid, action = uno.parse_action(v0, 0, "D")
        self.assertTrue(valid)
        self.assertEqual(action["type"], "draw")

        uno.apply_action(self.state, 0, action)
        self.assertEqual(len(self.state["hands"][0]), 8)


if __name__ == "__main__":
    unittest.main()
