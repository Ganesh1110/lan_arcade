"""
Lightweight, pure-Python QR Code generator for terminal display.
Zero dependencies. Generates QR Code Model 2 (Version 1 to 3) in ASCII block format.
"""

# GF(256) math for Reed-Solomon
_EXP = [0] * 512
_LOG = [0] * 256

def _init_gf256():
    x = 1
    for i in range(255):
        _EXP[i] = x
        _EXP[i + 255] = x
        _LOG[x] = i
        x = (x << 1) ^ (0x11D if (x & 0x80) else 0)

_init_gf256()

def _gf_mul(x, y):
    if x == 0 or y == 0:
        return 0
    return _EXP[_LOG[x] + _LOG[y]]

def _rs_poly(n_sym):
    poly = [1]
    for i in range(n_sym):
        factor = [1, _EXP[i]]
        new_poly = [0] * (len(poly) + 1)
        for j, c in enumerate(poly):
            new_poly[j] ^= _gf_mul(c, factor[0])
            new_poly[j + 1] ^= _gf_mul(c, factor[1])
        poly = new_poly
    return poly

def _rs_encode(data, n_sym):
    gen = _rs_poly(n_sym)
    res = list(data) + [0] * n_sym
    for i in range(len(data)):
        coef = res[i]
        if coef != 0:
            for j in range(1, len(gen)):
                res[i + j] ^= _gf_mul(gen[j], coef)
    return res[len(data):]

# Version capacities for Level L:
# V1: 19 data bytes, 7 ec bytes, size 21
# V2: 34 data bytes, 10 ec bytes, size 25
# V3: 55 data bytes, 15 ec bytes, size 29
_VERSIONS = [
    (1, 21, 19, 7),
    (2, 25, 34, 10),
    (3, 29, 55, 15),
]

_FORMAT_BITS = [
    # Level L format strings for masks 0-7 with BCH (15 bits)
    0x77C4, 0x72F3, 0x7DAA, 0x789D, 0x662F, 0x6318, 0x6C41, 0x6976
]

def generate_qr_matrix(text: str):
    """Generate a 2D boolean matrix (True=black/dark, False=white/light) for text."""
    raw = text.encode("utf-8")
    version = None
    for v, size, data_cap, ec_cap in _VERSIONS:
        # Byte mode header: 4 bits mode (0100) + 8 bits length = 12 bits -> 2 bytes overhead
        if len(raw) + 2 <= data_cap:
            version = (v, size, data_cap, ec_cap)
            break
    if not version:
        return None

    v_num, size, data_cap, ec_cap = version

    # Bitstream construction
    bits = []
    # Byte mode indicator: 0100
    bits.extend([0, 1, 0, 0])
    # Character count (8 bits for V1-3)
    for i in range(7, -1, -1):
        bits.append((len(raw) >> i) & 1)
    # Data bits
    for b in raw:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)

    # Terminator: up to 4 zero bits
    term_len = min(4, data_cap * 8 - len(bits))
    bits.extend([0] * term_len)

    # Pad to byte boundary
    while len(bits) % 8 != 0:
        bits.append(0)

    # Convert to bytes
    data_bytes = []
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        data_bytes.append(byte)

    # Pad codewords to data_cap
    pad = [0xEC, 0x11]
    pad_idx = 0
    while len(data_bytes) < data_cap:
        data_bytes.append(pad[pad_idx % 2])
        pad_idx += 1

    # Error correction codewords
    ec_bytes = _rs_encode(data_bytes, ec_cap)
    all_codewords = data_bytes + ec_bytes

    # Convert all codewords to bits
    final_bits = []
    for byte in all_codewords:
        for i in range(7, -1, -1):
            final_bits.append((byte >> i) & 1)

    # Matrix: None = unallocated, True = dark, False = light
    mat = [[None] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]

    def set_fn(r, c, val):
        mat[r][c] = val
        reserved[r][c] = True

    # Finder patterns
    def finder(r0, c0):
        for r in range(-1, 8):
            for c in range(-1, 8):
                if 0 <= r0 + r < size and 0 <= c0 + c < size:
                    is_black = (
                        (0 <= r <= 6 and (c == 0 or c == 6)) or
                        (0 <= c <= 6 and (r == 0 or r == 6)) or
                        (2 <= r <= 4 and 2 <= c <= 4)
                    )
                    set_fn(r0 + r, c0 + c, is_black)

    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)

    # Timing patterns
    for i in range(8, size - 8):
        set_fn(6, i, i % 2 == 0)
        set_fn(i, 6, i % 2 == 0)

    # Dark module
    set_fn(4 * v_num + 9, 8, True)

    # Reserve format info areas
    for i in range(9):
        if not reserved[8][i]:
            reserved[8][i] = True
        if not reserved[i][8]:
            reserved[i][8] = True
    for i in range(8):
        if not reserved[8][size - 1 - i]:
            reserved[8][size - 1 - i] = True
        if not reserved[size - 1 - i][8]:
            reserved[size - 1 - i][8] = True

    # Place data bits using upward/downward 2-column paths
    bit_idx = 0
    row, col = size - 1, size - 1
    direction = -1  # -1 = upward, +1 = downward

    while col > 0:
        if col == 6:  # Skip vertical timing pattern
            col -= 1
        for _ in range(size):
            for c in (col, col - 1):
                if not reserved[row][c]:
                    mat[row][c] = bool(final_bits[bit_idx]) if bit_idx < len(final_bits) else False
                    bit_idx += 1
            row += direction
        direction = -direction
        row += direction
        col -= 2

    # Best mask: mask 0 ( (row + col) % 2 == 0 ) is standard and widely supported
    mask_pattern = 0
    for r in range(size):
        for c in range(size):
            if not reserved[r][c]:
                if (r + c) % 2 == 0:
                    mat[r][c] = not mat[r][c]

    # Write format information (Mask 0 + Level L)
    fmt = _FORMAT_BITS[mask_pattern]
    fmt_bits = [(fmt >> i) & 1 for i in range(14, -1, -1)]

    # Format positions
    coords1 = (
        [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
         (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8)]
    )
    for idx, (r, c) in enumerate(coords1):
        mat[r][c] = bool(fmt_bits[idx])

    coords2 = (
        [(size - 1, 8), (size - 2, 8), (size - 3, 8), (size - 4, 8), (size - 5, 8),
         (size - 6, 8), (size - 7, 8), (8, size - 8), (8, size - 7), (8, size - 6),
         (8, size - 5), (8, size - 4), (8, size - 3), (8, size - 2), (8, size - 1)]
    )
    for idx, (r, c) in enumerate(coords2):
        mat[r][c] = bool(fmt_bits[idx])

    return mat


def render_qr_ascii(text: str, border: int = 1) -> str:
    """Render QR code to a compact 2-in-1 ASCII terminal string using unicode half-blocks."""
    mat = generate_qr_matrix(text)
    if not mat:
        return ""

    size = len(mat)
    # Add quiet zone border
    padded_size = size + 2 * border
    full = [[False] * padded_size for _ in range(padded_size)]
    for r in range(size):
        for c in range(size):
            full[r + border][c + border] = mat[r][c]

    lines = []
    # Each terminal line shows 2 matrix rows using half block character
    # ' ' = both light, '█' = both dark, '▀' = top dark/bottom light, '▄' = top light/bottom dark
    for r in range(0, padded_size, 2):
        row_str = []
        for c in range(padded_size):
            top = full[r][c]
            bot = full[r + 1][c] if r + 1 < padded_size else False
            if top and bot:
                row_str.append("█")
            elif top and not bot:
                row_str.append("▀")
            elif not top and bot:
                row_str.append("▄")
            else:
                row_str.append(" ")
        lines.append("  " + "".join(row_str))

    return "\n".join(lines)
