"""
Networking communication protocol using newline-delimited JSON messages.
"""
import json


class MessageType:
    JOIN = "join"
    JOINED = "joined"
    REJECT = "reject"
    LOBBY = "lobby"
    START = "start"
    TURN = "turn"
    CALL = "call"
    ACTION = "action"
    CALLED = "called"
    NOTICE = "notice"
    ERROR = "error"
    END = "end"


def encode_message(payload):
    """Serialize payload dictionary to newline-terminated UTF-8 JSON bytes."""
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


def decode_message(line):
    """Deserialize JSON string or line to payload dictionary."""
    if not line:
        return None
    try:
        data = json.loads(line)
        if isinstance(data, dict):
            return data
    except (ValueError, json.JSONDecodeError):
        pass
    return None
