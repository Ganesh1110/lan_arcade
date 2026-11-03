"""
Cross-platform Single Keypress and Direct Input Utility.
Allows instant steering via Arrow Keys and W/A/S/D without pressing [ENTER].
"""
import os
import sys
import select
from config import flush_stdin

IS_WINDOWS = (os.name == "nt")
if IS_WINDOWS:
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
else:
    try:
        import termios
        import tty
    except ImportError:
        termios = None
        tty = None


def read_direct_key(timeout=None):
    """
    Read a single keypress without waiting for [ENTER].
    Maps Arrow keys and WASD:
      Up / W    -> 'W'
      Down / S  -> 'S'
      Left / A  -> 'A'
      Right / D -> 'D'
      Space / Enter -> 'STRAIGHT'
      Q -> '!ff'
    If '!' is pressed, prompts for rest of chat line.
    Returns string action or None if timeout.
    """
    if not sys.stdin.isatty():
        try:
            line = sys.stdin.readline()
            return line.strip() if line else None
        except Exception:
            return None

    # --- Windows Implementation ---
    if IS_WINDOWS and msvcrt:
        import time
        t_end = (time.time() + timeout) if timeout else None
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                # Special keys / arrow keys on Windows prefix \x00 or \xe0
                if ch in (b"\x00", b"\xe0"):
                    ch2 = msvcrt.getch()
                    if ch2 == b"H": return "W"  # Up
                    if ch2 == b"P": return "S"  # Down
                    if ch2 == b"K": return "A"  # Left
                    if ch2 == b"M": return "D"  # Right
                else:
                    char_str = ch.decode("utf-8", errors="ignore")
                    if char_str.upper() in {"W", "A", "S", "D"}:
                        return char_str.upper()
                    if char_str in {"\r", "\n", " "}:
                        return "STRAIGHT"
                    if char_str.upper() in {"Q"}:
                        return "!ff"
                    if char_str == "!":
                        sys.stdout.write("!")
                        sys.stdout.flush()
                        rest = input()
                        return "!" + rest
                    return char_str
            if t_end and time.time() >= t_end:
                return None
            time.sleep(0.02)

    # --- POSIX (macOS / Linux) Implementation ---
    elif termios and tty:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            r, _, _ = select.select([sys.stdin], [], [], timeout)
            if not r:
                return None

            ch = sys.stdin.read(1)
            # Check ANSI escape sequence for Arrow keys: \x1b[A, \x1b[B, \x1b[C, \x1b[D
            if ch == "\x1b":
                r2, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r2:
                    ch2 = sys.stdin.read(1)
                    if ch2 in ("[", "O"):
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A": return "W"  # Up
                        if ch3 == "B": return "S"  # Down
                        if ch3 == "C": return "D"  # Right
                        if ch3 == "D": return "A"  # Left
                return None

            if ch.upper() in {"W", "A", "S", "D"}:
                return ch.upper()
            if ch in {"\r", "\n", " "}:
                return "STRAIGHT"
            if ch.upper() in {"Q"}:
                return "!ff"
            if ch == "!":
                # Restore settings temporarily to read full chat line
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.write("!")
                sys.stdout.flush()
                rest = input()
                return "!" + rest

            return ch
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                pass

    # Fallback to standard input
    try:
        return input().strip()
    except Exception:
        return None
