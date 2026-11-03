"""
Unit tests for LAN discovery mechanisms.
"""
import json
import unittest
from utils.discovery import discover_hosts


class TestDiscovery(unittest.TestCase):
    def test_discovery_safe_fallback(self):
        # Discover should safely return a list without unhandled exceptions
        res = discover_hosts(timeout=0.1)
        self.assertIsInstance(res, list)

    def test_beacon_packet_structure(self):
        payload = {
            "type": "arcade_beacon",
            "room": "Test Room",
            "game": "Connect Four",
            "ip": "192.168.1.100",
            "port": 50555,
            "players": 1,
            "max": 2
        }
        encoded = json.dumps(payload).encode("utf-8")
        decoded = json.loads(encoded.decode("utf-8"))
        self.assertEqual(decoded["type"], "arcade_beacon")
        self.assertEqual(decoded["game"], "Connect Four")
        self.assertEqual(decoded["port"], 50555)


if __name__ == "__main__":
    unittest.main()
