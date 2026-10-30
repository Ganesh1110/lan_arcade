"""
Input validation utilities.
"""


def clean_name(raw, default="Player"):
    """Sanitize player name string."""
    name = "".join(ch for ch in str(raw) if ch.isprintable()).strip()[:20]
    return name or default


def parse_int(raw, min_val=None, max_val=None):
    """Parse raw string into integer within optional bounds."""
    try:
        val = int(str(raw).strip())
        if min_val is not None and val < min_val:
            return None
        if max_val is not None and val > max_val:
            return None
        return val
    except (ValueError, TypeError):
        return None


def parse_coordinate(raw, rows=5, cols=5):
    """
    Parse a grid coordinate string like 'C3' or 'A1' into 0-indexed (row, col).
    Column is letter (A, B, C...), row is number (1, 2, 3...).
    Returns (row, col) or None if invalid.
    """
    text = str(raw).strip().upper()
    if len(text) < 2:
        return None
    col_char = text[0]
    row_text = text[1:]

    if not col_char.isalpha() or not row_text.isdigit():
        return None

    col = ord(col_char) - ord('A')
    row = int(row_text) - 1

    if 0 <= row < rows and 0 <= col < cols:
        return (row, col)
    return None
