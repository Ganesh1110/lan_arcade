"""
Configuration settings for College LAN Arcade.
"""
import os
import sys

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 50555
MAX_PLAYERS = 4
BUFFER_SIZE = 4096
SOCKET_TIMEOUT = 10.0

USE_COLOR = sys.stdout.isatty()
if USE_COLOR and os.name == "nt":
    os.system("")  # Enable ANSI color support on Windows console


def paint(value, code):
    """Wrap value in ANSI color escape sequence if color is supported."""
    return f"\033[{code}m{value}\033[0m" if USE_COLOR else str(value)


def clear_screen():
    """Clear terminal screen in a cross-platform manner."""
    if not USE_COLOR:
        return
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[2J\033[3J\033[H")
        sys.stdout.flush()


def flush_stdin():
    """Discard pending unread user input from stdin buffer."""
    try:
        if os.name == "nt":
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getwch()
        else:
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass
