"""
Custom exception classes for College LAN Arcade.
"""


class ArcadeError(Exception):
    """Base exception for all arcade errors."""
    pass


class NetworkError(ArcadeError):
    """Raised on socket connection or network transmission failures."""
    pass


class LobbyError(ArcadeError):
    """Raised on room or lobby management issues."""
    pass


class InvalidMoveError(ArcadeError):
    """Raised when a player attempts an invalid action."""
    pass
