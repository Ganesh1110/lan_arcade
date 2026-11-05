"""
Full 8x8 Chess Game Module.
2-Player Competitive Classic Chess with standard movement rules and check detection.
"""
import copy
from config import paint

game_id = "chess"
game_name = "Chess"
min_players = 2
max_players = 2

# Piece Unicode symbols and labels
WHITE_PIECES = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙"
}
BLACK_PIECES = {
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"
}

# High-clarity coin representations (Piece glyph + uppercase/lowercase piece letter)
# Completely eliminates confusion between Bishop (B/b) and Soldier/Pawn (P/p)
WHITE_COINS = {
    "K": "♔ K", "Q": "♕ Q", "R": "♖ R", "B": "♗ B", "N": "♘ N", "P": "♙ P"
}
BLACK_COINS = {
    "k": "♚ k", "q": "♛ q", "r": "♜ r", "b": "♝ b", "n": "♞ n", "p": "♟ p"
}

PIECE_VALUES = {
    "p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100,
    "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100
}

FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]


def initial_board():
    """Create starting 8x8 standard chess layout."""
    # Row 0 = Rank 8 (Black), Row 7 = Rank 1 (White)
    return [
        ["r", "n", "b", "q", "k", "b", "n", "r"],  # Rank 8
        ["p", "p", "p", "p", "p", "p", "p", "p"],  # Rank 7
        [None] * 8,                                # Rank 6
        [None] * 8,                                # Rank 5
        [None] * 8,                                # Rank 4
        [None] * 8,                                # Rank 3
        ["P", "P", "P", "P", "P", "P", "P", "P"],  # Rank 2
        ["R", "N", "B", "Q", "K", "B", "N", "R"],  # Rank 1
    ]


def parse_coord(coord_str):
    """Convert chess notation (e.g. 'e4') to (row, col) (0-7)."""
    s = coord_str.strip().lower()
    if len(s) != 2:
        return None
    file_char, rank_char = s[0], s[1]
    if file_char not in FILES or not rank_char.isdigit():
        return None
    col = FILES.index(file_char)
    rank = int(rank_char)
    if not (1 <= rank <= 8):
        return None
    row = 8 - rank
    return (row, col)


def to_coord(row, col):
    """Convert (row, col) back to chess notation (e.g. 'e4')."""
    return f"{FILES[col]}{8 - row}"


def is_white_piece(piece):
    return piece is not None and piece.isupper()


def is_black_piece(piece):
    return piece is not None and piece.islower()


def is_path_clear(board, r1, c1, r2, c2):
    """Verify that all squares between (r1, c1) and (r2, c2) are empty."""
    dr = 0 if r1 == r2 else (1 if r2 > r1 else -1)
    dc = 0 if c1 == c2 else (1 if c2 > c1 else -1)
    curr_r = r1 + dr
    curr_c = c1 + dc
    while (curr_r, curr_c) != (r2, c2):
        if board[curr_r][curr_c] is not None:
            return False
        curr_r += dr
        curr_c += dc
    return True


def is_square_attacked(board, target_r, target_c, by_white):
    """Check whether square (target_r, target_c) is under attack by pieces of by_white color."""
    pawn_char = "P" if by_white else "p"
    knight_char = "N" if by_white else "n"
    bishop_char = "B" if by_white else "b"
    rook_char = "R" if by_white else "r"
    queen_char = "Q" if by_white else "q"
    king_char = "K" if by_white else "k"

    # 1. Pawn attacks
    # If attacked by white, white pawns come from row target_r + 1
    pawn_dr = 1 if by_white else -1
    pr = target_r + pawn_dr
    if 0 <= pr < 8:
        for pc in [target_c - 1, target_c + 1]:
            if 0 <= pc < 8 and board[pr][pc] == pawn_char:
                return True

    # 2. Knight attacks
    knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, dc in knight_offsets:
        nr, nc = target_r + dr, target_c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == knight_char:
            return True

    # 3. King attacks (adjacent 1 square)
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            kr, kc = target_r + dr, target_c + dc
            if 0 <= kr < 8 and 0 <= kc < 8 and board[kr][kc] == king_char:
                return True

    # 4. Straight line attacks (Rook, Queen)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        step = 1
        while True:
            rr, rc = target_r + dr * step, target_c + dc * step
            if not (0 <= rr < 8 and 0 <= rc < 8):
                break
            sq_piece = board[rr][rc]
            if sq_piece is not None:
                if sq_piece == rook_char or sq_piece == queen_char:
                    return True
                break
            step += 1

    # 5. Diagonal line attacks (Bishop, Queen)
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        step = 1
        while True:
            br, bc = target_r + dr * step, target_c + dc * step
            if not (0 <= br < 8 and 0 <= bc < 8):
                break
            sq_piece = board[br][bc]
            if sq_piece is not None:
                if sq_piece == bishop_char or sq_piece == queen_char:
                    return True
                break
            step += 1

    return False


def is_valid_piece_move(board, r1, c1, r2, c2, is_white, state=None):
    """Validate movement rules according to piece geometry, castling, and en passant."""
    piece = board[r1][c1]
    if piece is None:
        return False, "No piece at starting square."

    target = board[r2][c2]
    # Cannot capture your own piece
    if target is not None:
        if is_white and is_white_piece(target):
            return False, "Cannot capture your own piece."
        if not is_white and is_black_piece(target):
            return False, "Cannot capture your own piece."

    dr = r2 - r1
    dc = c2 - c1
    p_upper = piece.upper()

    # --- PAWN ---
    if p_upper == "P":
        direction = -1 if is_white else 1
        start_row = 6 if is_white else 1
        # Forward 1
        if dc == 0 and dr == direction and target is None:
            return True, None
        # Forward 2 from start row
        if dc == 0 and dr == 2 * direction and r1 == start_row and target is None:
            if board[r1 + direction][c1] is None:
                return True, None
        # Diagonal capture
        if abs(dc) == 1 and dr == direction and target is not None:
            return True, None
        # En Passant
        if abs(dc) == 1 and dr == direction and target is None:
            if state and state.get("en_passant_target") == (r2, c2):
                return True, None
        return False, "Invalid pawn move."

    # --- KNIGHT ---
    elif p_upper == "N":
        if (abs(dr) == 1 and abs(dc) == 2) or (abs(dr) == 2 and abs(dc) == 1):
            return True, None
        return False, "Knights must move in an L-shape (2 by 1 squares)."

    # --- BISHOP ---
    elif p_upper == "B":
        if abs(dr) == abs(dc) and abs(dr) > 0:
            if is_path_clear(board, r1, c1, r2, c2):
                return True, None
            return False, "Path is blocked by another piece."
        return False, "Bishops move diagonally."

    # --- ROOK ---
    elif p_upper == "R":
        if (dr == 0 and dc != 0) or (dc == 0 and dr != 0):
            if is_path_clear(board, r1, c1, r2, c2):
                return True, None
            return False, "Path is blocked by another piece."
        return False, "Rooks move horizontally or vertically."

    # --- QUEEN ---
    elif p_upper == "Q":
        is_diag = abs(dr) == abs(dc) and abs(dr) > 0
        is_straight = (dr == 0 and dc != 0) or (dc == 0 and dr != 0)
        if is_diag or is_straight:
            if is_path_clear(board, r1, c1, r2, c2):
                return True, None
            return False, "Path is blocked by another piece."
        return False, "Queens move in any straight or diagonal line."

    # --- KING ---
    elif p_upper == "K":
        # Normal 1 square step
        if max(abs(dr), abs(dc)) == 1:
            return True, None

        # Castling
        if dr == 0 and abs(dc) == 2:
            rank = 7 if is_white else 0
            if r1 != rank:
                return False, "Castling is only allowed from king's starting rank."
            has_moved = state.get("has_moved", {}) if isinstance(state, dict) else {}
            king_key = "K" if is_white else "k"
            if has_moved.get(king_key, False):
                return False, "King has already moved; castling unavailable."
            if is_king_in_check(board, is_white):
                return False, "Cannot castle out of CHECK."

            # Kingside (O-O)
            if dc == 2:
                r_key = "R_h1" if is_white else "r_h8"
                expected_rook = "R" if is_white else "r"
                if has_moved.get(r_key, False) or board[rank][7] != expected_rook:
                    return False, "Kingside rook has moved or is absent."
                if board[rank][5] is not None or board[rank][6] is not None:
                    return False, "Path between king and kingside rook is blocked."
                if is_square_attacked(board, rank, 5, not is_white) or is_square_attacked(board, rank, 6, not is_white):
                    return False, "Cannot castle through or into a square under attack."
                return True, None

            # Queenside (O-O-O)
            elif dc == -2:
                r_key = "R_a1" if is_white else "r_a8"
                expected_rook = "R" if is_white else "r"
                if has_moved.get(r_key, False) or board[rank][0] != expected_rook:
                    return False, "Queenside rook has moved or is absent."
                if board[rank][1] is not None or board[rank][2] is not None or board[rank][3] is not None:
                    return False, "Path between king and queenside rook is blocked."
                if is_square_attacked(board, rank, 3, not is_white) or is_square_attacked(board, rank, 2, not is_white):
                    return False, "Cannot castle through or into a square under attack."
                return True, None

        return False, "Kings move 1 square in any direction, or 2 squares to castle."

    return False, "Unknown piece move."


def find_king(board, is_white):
    """Find (row, col) position of the king."""
    target_k = "K" if is_white else "k"
    for r in range(8):
        for c in range(8):
            if board[r][c] == target_k:
                return (r, c)
    return None


def is_king_in_check(board, is_white):
    """Check if the given side's king is currently under attack."""
    k_pos = find_king(board, is_white)
    if not k_pos:
        return True  # King captured
    return is_square_attacked(board, k_pos[0], k_pos[1], not is_white)


def get_legal_moves(board, is_white, state=None):
    """Generate all strictly legal moves for the given side (king left out of check)."""
    legal_moves = []
    for r1 in range(8):
        for c1 in range(8):
            p = board[r1][c1]
            if p is None:
                continue
            if is_white and not is_white_piece(p):
                continue
            if not is_white and not is_black_piece(p):
                continue

            for r2 in range(8):
                for c2 in range(8):
                    valid, _ = is_valid_piece_move(board, r1, c1, r2, c2, is_white, state)
                    if not valid:
                        continue

                    # Simulate move
                    tb = copy.deepcopy(board)
                    moving_p = tb[r1][c1]
                    tb[r2][c2] = moving_p
                    tb[r1][c1] = None

                    # Simulate en passant capture removal
                    if moving_p.upper() == "P" and state and state.get("en_passant_target") == (r2, c2) and abs(c2 - c1) == 1:
                        tb[r1][c2] = None

                    # Simulate castling rook movement
                    if moving_p.upper() == "K" and abs(c2 - c1) == 2:
                        if c2 == 6:
                            tb[r1][5] = tb[r1][7]
                            tb[r1][7] = None
                        elif c2 == 2:
                            tb[r1][3] = tb[r1][0]
                            tb[r1][0] = None

                    if not is_king_in_check(tb, is_white):
                        legal_moves.append({"from": (r1, c1), "to": (r2, c2)})

    return legal_moves


def _get_position_key(board, next_turn_is_white, state):
    board_tuple = tuple(tuple(row) for row in board)
    has_moved = state.get("has_moved", {})
    castling_rights = (
        not has_moved.get("K", False) and not has_moved.get("R_h1", False),
        not has_moved.get("K", False) and not has_moved.get("R_a1", False),
        not has_moved.get("k", False) and not has_moved.get("r_h8", False),
        not has_moved.get("k", False) and not has_moved.get("r_a8", False),
    )
    ep_target = state.get("en_passant_target")
    return (board_tuple, next_turn_is_white, castling_rights, ep_target)


def _check_insufficient_material(board):
    white_minors = []
    black_minors = []
    bishops = []
    knights = []

    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p:
                continue
            if p.upper() in ("P", "R", "Q"):
                return False
            if p.isupper():
                if p != "K":
                    white_minors.append(p)
                    if p == "B":
                        bishops.append(("White", r, c))
                    elif p == "N":
                        knights.append(("White", r, c))
            else:
                if p != "k":
                    black_minors.append(p)
                    if p == "b":
                        bishops.append(("Black", r, c))
                    elif p == "n":
                        knights.append(("Black", r, c))

    # If there are no knights on the board and all bishops are on the same square color
    # (covers K vs K with 0 bishops, K+B vs K with 1 bishop, K+B vs K+B on same color,
    # or several bishops all on the same color complex)
    if len(knights) == 0:
        square_colors = {(r + c) % 2 for _, r, c in bishops}
        if len(square_colors) <= 1:
            return True

    # K+N vs K (1 knight, 0 bishops)
    if len(bishops) == 0 and len(knights) == 1:
        return True

    return False


def create_state(player_sessions):
    players = []
    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        side = "White" if idx == 0 else "Black"
        color = "1;37" if idx == 0 else "1;33"
        players.append({"id": pid, "name": name, "side": side, "color": color})

    board = initial_board()
    st = {
        "players": players,
        "board": board,
        "turn_index": 0,
        "has_moved": {"K": False, "k": False, "R_a1": False, "R_h1": False, "r_a8": False, "r_h8": False},
        "en_passant_target": None,
        "captured_white": [],  # Black pieces captured by White
        "captured_black": [],  # White pieces captured by Black
        "moves_history": [],
        "halfmove_clock": 0,
        "position_counts": {},
        "in_check": False,
        "winner": None,
        "log": ["♔ Chess match started! White moves first."]
    }
    init_key = _get_position_key(board, True, st)
    st["position_counts"][init_key] = 1
    return st


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "side": p_data["side"] if p_data else "White",
        "opponent_name": opp["name"] if opp else "Opponent",
        "players": state["players"],
        "board": state["board"],
        "turn_id": current_player(state),
        "turn_index": state.get("turn_index", 0),
        "captured_white": state["captured_white"],
        "captured_black": state["captured_black"],
        "moves_history": state["moves_history"],
        "in_check": state.get("in_check", False),
        "has_moved": state.get("has_moved", {}),
        "en_passant_target": state.get("en_passant_target"),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter move: 'e2e4', 'e2-e4', 'Nf3', 'O-O' (castle), or 'e7e8q' (promotion)"


def parse_action(state_or_view, player_id, raw_input):
    raw = str(raw_input).strip()
    if not raw:
        return False, "Move cannot be empty."

    board = state_or_view.get("board") if isinstance(state_or_view, dict) else state_or_view.state["board"]
    players = state_or_view.get("players", [])
    p_white = players[0]["id"] if players else 0
    is_white_turn = (player_id == p_white)

    legal_moves = get_legal_moves(board, is_white_turn, state_or_view)
    if not legal_moves:
        return False, "No legal moves available."

    candidate = None
    prom_choice = "Q"

    # 1. Castling shorthand
    if raw.upper() in {"O-O", "0-0"}:
        rank = 7 if is_white_turn else 0
        candidate = {"from": (rank, 4), "to": (rank, 6)}
    elif raw.upper() in {"O-O-O", "0-0-0"}:
        rank = 7 if is_white_turn else 0
        candidate = {"from": (rank, 4), "to": (rank, 2)}
    else:
        # Check promotion suffix e.g. e7e8=Q or e7e8q
        clean_raw = raw.replace(" ", "").replace("-", "").replace("to", "")
        if "=" in clean_raw:
            parts = clean_raw.split("=")
            clean_raw = parts[0]
            if len(parts) > 1 and parts[1].upper() in {"Q", "R", "B", "N"}:
                prom_choice = parts[1].upper()
        elif len(clean_raw) == 5 and clean_raw[4].upper() in {"Q", "R", "B", "N"}:
            prom_choice = clean_raw[4].upper()
            clean_raw = clean_raw[:4]

        # 2. Coordinate format e.g. 'e2e4'
        if len(clean_raw) == 4:
            from_str = clean_raw[:2].lower()
            to_str = clean_raw[2:4].lower()
            c1 = parse_coord(from_str)
            c2 = parse_coord(to_str)
            if c1 and c2:
                candidate = {"from": c1, "to": c2}

        # 3. Standard Algebraic Notation (SAN) e.g. 'Nf3', 'e4', 'Bxf7', 'Qh5', 'exd5'
        if not candidate:
            san = raw.replace("+", "").replace("#", "").replace("x", "").replace("X", "").strip()
            if len(san) >= 2:
                target_str = san[-2:].lower()
                c2 = parse_coord(target_str)
                if c2:
                    piece_type = san[0].upper() if san[0].isupper() else "P"
                    disambig = san[1:-2].lower() if san[0].isupper() else san[:-2].lower()

                    matches = []
                    for m in legal_moves:
                        if m["to"] == c2:
                            r1, col1 = m["from"]
                            p = board[r1][col1]
                            if p and p.upper() == piece_type:
                                # Check disambiguation (file or rank)
                                if disambig:
                                    f_char = FILES[col1]
                                    r_char = str(8 - r1)
                                    if disambig not in (f_char, r_char, f"{f_char}{r_char}"):
                                        continue
                                matches.append(m)

                    if len(matches) == 1:
                        candidate = matches[0]
                    elif len(matches) > 1:
                        return False, f"Ambiguous move '{raw}'. Specify starting square (e.g. 'Nbd2')."

    if not candidate:
        return False, f"Could not parse chess move '{raw}'. Use e.g. 'e2e4', 'Nf3', or 'O-O'."

    # Verify candidate is strictly legal
    r1, col1 = candidate["from"]
    r2, col2 = candidate["to"]
    is_legal = any(m["from"] == (r1, col1) and m["to"] == (r2, col2) for m in legal_moves)

    if not is_legal:
        valid_geom, err = is_valid_piece_move(board, r1, col1, r2, col2, is_white_turn, state_or_view)
        if not valid_geom:
            return False, err or "Illegal move."
        return False, "Illegal move: King would be in CHECK."

    return True, {
        "from": (r1, col1),
        "to": (r2, col2),
        "promotion": prom_choice,
        "notation": f"{to_coord(r1, col1)}{to_coord(r2, col2)}"
    }


def apply_action(state, player_id, action_data):
    r1, c1 = action_data["from"]
    r2, c2 = action_data["to"]
    board = state["board"]
    piece = board[r1][c1]
    target = board[r2][c2]

    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    opp = next(p for p in state["players"] if p["id"] != player_id)
    p_name = curr_p["name"]
    opp_name = opp["name"]
    is_white = (curr_p["side"] == "White")
    log_entries = []

    # Handle En Passant capture
    if piece.upper() == "P" and state.get("en_passant_target") == (r2, c2) and target is None and abs(c2 - c1) == 1:
        ep_r = r1
        ep_c = c2
        target = board[ep_r][ep_c]
        board[ep_r][ep_c] = None

    # Handle Castling rook movement
    if piece.upper() == "K" and abs(c2 - c1) == 2:
        if c2 == 6:  # Kingside
            board[r1][5] = board[r1][7]
            board[r1][7] = None
            state.setdefault("has_moved", {})["R_h1" if is_white else "r_h8"] = True
        elif c2 == 2:  # Queenside
            board[r1][3] = board[r1][0]
            board[r1][0] = None
            state.setdefault("has_moved", {})["R_a1" if is_white else "r_a8"] = True

    # Handle Capture logging and collection
    if target is not None:
        if is_white:
            state["captured_white"].append(target)
        else:
            state["captured_black"].append(target)

    # Move piece to destination
    board[r2][c2] = piece
    board[r1][c1] = None

    # Pawn Promotion
    promoted = False
    prom_piece = action_data.get("promotion", "Q").upper()
    if piece == "P" and r2 == 0:
        board[r2][c2] = prom_piece
        promoted = True
    elif piece == "p" and r2 == 7:
        board[r2][c2] = prom_piece.lower()
        promoted = True

    # Update en_passant_target for double-step pawn advance
    direction = -1 if is_white else 1
    if piece.upper() == "P" and abs(r2 - r1) == 2:
        state["en_passant_target"] = (r1 + direction, c1)
    else:
        state["en_passant_target"] = None

    # Update has_moved tracking
    if piece == "K":
        state.setdefault("has_moved", {})["K"] = True
    elif piece == "k":
        state.setdefault("has_moved", {})["k"] = True
    elif (r1, c1) == (7, 0):
        state.setdefault("has_moved", {})["R_a1"] = True
    elif (r1, c1) == (7, 7):
        state.setdefault("has_moved", {})["R_h1"] = True
    elif (r1, c1) == (0, 0):
        state.setdefault("has_moved", {})["r_a8"] = True
    elif (r1, c1) == (0, 7):
        state.setdefault("has_moved", {})["r_h8"] = True

    # Record notation
    notat = f"{to_coord(r1, c1)}➔{to_coord(r2, c2)}"
    if target:
        notat += f" (x{target.upper()})"
    if promoted:
        notat += f"={prom_piece}"

    state["moves_history"].append(f"{curr_p['side'][:1]}: {notat}")

    # 50-move clock: reset on pawn move or capture
    if target is not None or piece.upper() == "P":
        state["halfmove_clock"] = 0
    else:
        state["halfmove_clock"] = state.get("halfmove_clock", 0) + 1

    # Check opponent check / checkmate / stalemate status
    opp_is_white = not is_white
    opp_moves = get_legal_moves(board, opp_is_white, state)
    opp_in_check = is_king_in_check(board, opp_is_white)
    state["in_check"] = opp_in_check

    move_log = f"♟ {p_name} ({curr_p['side']}) played {notat}."
    if opp_in_check:
        move_log += " ⚠️ CHECK!"
    log_entries.append(move_log)

    if not opp_moves:
        if opp_in_check:
            state["winner"] = [p_name]
            log_entries.append(f"🏆 CHECKMATE! {p_name} ({curr_p['side']}) wins the game!")
        else:
            state["winner"] = []
            log_entries.append(f"🤝 STALEMATE! {opp_name} has no legal moves. Match is drawn.")
    elif state.get("winner") is None:
        # Check insufficient material
        if _check_insufficient_material(board):
            state["winner"] = []
            log_entries.append("🤝 DRAW! Insufficient material to checkmate.")
        # Check 50-move rule
        elif state.get("halfmove_clock", 0) >= 100:
            state["winner"] = []
            log_entries.append("🤝 DRAW! Fifty-move rule (50 moves without capture or pawn advance).")
        else:
            # Check threefold repetition
            pos_key = _get_position_key(board, opp_is_white, state)
            state.setdefault("position_counts", {})
            state["position_counts"][pos_key] = state["position_counts"].get(pos_key, 0) + 1
            if state["position_counts"][pos_key] >= 3:
                state["winner"] = []
                log_entries.append("🤝 DRAW! Threefold repetition of position.")

    state["turn_index"] += 1
    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state.get("winner") is not None


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def _format_captured_coins(cap_list, is_white_capturer):
    if not cap_list:
        return "None"
    coins_map = BLACK_COINS if is_white_capturer else WHITE_COINS
    counts = {}
    for p in cap_list:
        counts[p] = counts.get(p, 0) + 1
    order = ["q", "r", "b", "n", "p"] if is_white_capturer else ["Q", "R", "B", "N", "P"]
    items = []
    for p in order:
        if p in counts:
            coin = coins_map.get(p, p)
            cnt = counts[p]
            items.append(f"{coin}×{cnt}" if cnt > 1 else coin)
    return "  ".join(items) if items else "None"


def _render_chess_board(board, last_src=None, last_dest=None, checked_king=None):
    lines = []
    files_header = "      A     B     C     D     E     F     G     H"
    border_top  = "   ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐"
    border_mid  = "   ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤"
    border_bot  = "   └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘"

    lines.append(paint(files_header, "1;36"))
    lines.append(border_top)

    for r in range(8):
        rank_num = 8 - r
        row_cells = []
        for c in range(8):
            piece = board[r][c]
            is_light_sq = ((r + c) % 2 == 0)
            is_last_src = (last_src == (r, c))
            is_last_dst = (last_dest == (r, c))
            is_king_check = (checked_king == (r, c))

            if piece is None:
                if is_last_src:
                    styled = paint("  ◇  ", "1;32")
                else:
                    cell_content = "  ·  " if is_light_sq else "     "
                    styled = paint(cell_content, "2;37")
            else:
                if piece.isupper():
                    coin = WHITE_COINS.get(piece, f"{piece}  ")
                    if is_king_check:
                        styled = paint(f" {coin} ", "1;37;41")  # Checked king alert
                    elif is_last_dst:
                        styled = paint(f" {coin} ", "1;97;42")  # Destination square highlight
                    else:
                        styled = paint(f" {coin} ", "1;37;44")  # White piece on blue cell
                else:
                    coin = BLACK_COINS.get(piece, f"{piece}  ")
                    if is_king_check:
                        styled = paint(f" {coin} ", "1;33;41")  # Checked king alert
                    elif is_last_dst:
                        styled = paint(f" {coin} ", "1;33;42")  # Destination square highlight
                    else:
                        styled = paint(f" {coin} ", "1;33;41")  # Black piece on red cell

            row_cells.append(styled)

        lines.append(f" {rank_num} │" + "│".join(row_cells) + f"│ {rank_num}")
        if r < 7:
            lines.append(border_mid)
        else:
            lines.append(border_bot)

    lines.append(paint(files_header, "1;36"))
    return "\n".join(lines)


def render_dashboard(view):
    players = view.get("players", [])
    board = view.get("board", initial_board())
    turn_id = view.get("turn_id")
    in_check = view.get("in_check", False)
    captured_w = view.get("captured_white", [])
    captured_b = view.get("captured_black", [])
    moves = view.get("moves_history", [])
    log = view.get("log", [])

    # Extract last move coordinates for board highlighting
    last_src = None
    last_dest = None
    if moves:
        last_m = moves[-1]
        parts = last_m.split("➔")
        if len(parts) == 2:
            src_str = parts[0][-2:].strip().lower()
            dst_str = parts[1][:2].strip().lower()
            last_src = parse_coord(src_str)
            last_dest = parse_coord(dst_str)

    # Determine which King is under check
    checked_king = None
    if in_check:
        curr_turn_side = "White"
        for p in players:
            if p["id"] == turn_id:
                curr_turn_side = p.get("side", "White")
                break
        checked_king = find_king(board, is_white=(curr_turn_side == "White"))

    # Material calculations
    sc_w = sum(PIECE_VALUES.get(p, 0) for p in captured_w)
    sc_b = sum(PIECE_VALUES.get(p, 0) for p in captured_b)
    diff = sc_w - sc_b
    lead_w = f" {paint(f'(+{diff} material lead)', '1;32')}" if diff > 0 else ""
    lead_b = f" {paint(f'(+{abs(diff)} material lead)', '1;32')}" if diff < 0 else ""

    out = [
        paint("=" * 56, "1;36"),
        paint("                 C H E S S   A R C A D E", "1;36"),
        paint("=" * 56, "1;36"),
        ""
    ]

    # Captured pieces summary with clear coin labels and point advantage
    cap_w_str = _format_captured_coins(captured_w, True)
    cap_b_str = _format_captured_coins(captured_b, False)
    out.append(f"  Captured by White: {paint(cap_w_str, '1;33')}{lead_w}")
    out.append(f"  Captured by Black: {paint(cap_b_str, '1;37')}{lead_b}")
    out.append("")

    # Enhanced Chessboard with move tracking and check highlighting
    out.append(_render_chess_board(board, last_src, last_dest, checked_king))
    out.append("")

    # High-clarity Coin Legend
    out.append("  " + paint("COIN GUIDE:", "1;33") + "  ♔/♚ King (K)    ♕/♛ Queen (Q)    ♖/✜ Rook (R)")
    out.append("               ♗/♝ Bishop (B)  ♘/♞ Knight (N)   ♙/♟ Soldier/Pawn (P)")
    out.append("")

    if in_check:
        out.append(paint("  ⚠️  CHECK! King is under direct attack!", "1;31"))
        out.append("")

    # Players
    out.append("  PLAYERS:")
    for p in players:
        pid = p["id"]
        side = p.get("side", "White")
        color = p.get("color", "1;37")
        is_turn = (pid == turn_id)
        ptr = paint("▶", "1;32") if is_turn else " "
        tag = " " + paint("◀ CURRENT TURN", "1;36") if is_turn else ""
        icon = "♔" if side == "White" else "♚"
        out.append(f"   {ptr} {paint(icon, color)} {paint(side.upper(), color):<6} : {p['name']:<18}{tag}")

    # Recent moves ticker
    if moves:
        out.append("")
        out.append("  Recent Moves: " + " | ".join(moves[-4:]))

    if log:
        out.append("")
        out.append("  Recent Activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  CHECKMATE! WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Game ended in a Draw / Stalemate.", "1;33"))
    return "\n".join(parts)
