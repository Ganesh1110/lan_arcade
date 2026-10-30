import unittest
from games import dots_and_boxes


class TestDotsAndBoxes(unittest.TestCase):
    def setUp(self):
        sessions = [{"id": 0, "name": "P1"}, {"id": 1, "name": "P2"}]
        self.state = dots_and_boxes.create_state(sessions)

    def test_place_edge(self):
        v0 = dots_and_boxes.view_for(self.state, 0)
        valid, act = dots_and_boxes.parse_action(v0, 0, "H 1 1")
        self.assertTrue(valid)

        dots_and_boxes.apply_action(self.state, 0, act)
        self.assertTrue(self.state["h_edges"][0][0])
        self.assertEqual(self.state["total_lines"], 1)


if __name__ == "__main__":
    unittest.main()
