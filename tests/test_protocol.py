import unittest
from protocol import encode_message, decode_message, MessageType


class TestProtocol(unittest.TestCase):
    def test_encode_decode(self):
        payload = {"type": MessageType.JOIN, "name": "Ganesh"}
        encoded = encode_message(payload)
        self.assertTrue(encoded.endswith(b"\n"))
        decoded = decode_message(encoded.decode("utf-8"))
        self.assertEqual(decoded["type"], "join")
        self.assertEqual(decoded["name"], "Ganesh")

    def test_invalid_decode(self):
        self.assertIsNone(decode_message(""))
        self.assertIsNone(decode_message("invalid json {"))


if __name__ == "__main__":
    unittest.main()
