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


def is_valid_piece_move(board, r1, c1, r2, c2, is_white):
    """Validate movement rules according to piece geometry."""
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
        if max(abs(dr), abs(dc)) == 1:
            return True, None
        return False, "Kings can only move 1 square in any direction."

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
    kr, kc = k_pos

    # Check if any enemy piece can attack the king
    enemy_is_white = not is_white
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is None:
                continue
            if is_white and is_black_piece(piece):
                valid, _ = is_valid_piece_move(board, r, c, kr, kc, enemy_is_white)
                if valid:
                    return True
            elif not is_white and is_white_piece(piece):
                valid, _ = is_valid_piece_move(board, r, c, kr, kc, enemy_is_white)
                if valid:
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

    return {
        "players": players,
        "board": initial_board(),
        "turn_index": 0,
        "captured_white": [],  # Black pieces captured by White
        "captured_black": [],  # White pieces captured by Black
        "moves_history": [],
        "in_check": False,
        "winner": None,
        "log": ["♔ Chess match started! White moves first."]
    }


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
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter move in coordinates, e.g. 'e2e4', 'e2-e4', or 'Nf3'"


def parse_action(state_or_view, player_id, raw_input):
    cleaned = str(raw_input).strip().replace(" ", "").replace("-", "").replace("to", "").lower()
    if len(cleaned) < 4:
        return False, "Move format must be e.g. 'e2e4' or 'e2-e4'."

    from_str = cleaned[:2]
    to_str = cleaned[2:4]

    c1 = parse_coord(from_str)
    c2 = parse_coord(to_str)

    if not c1 or not c2:
        return False, f"Invalid coordinates '{from_str}' -> '{to_str}' (files a–h, ranks 1–8)."

    if c1 == c2:
        return False, "Starting and destination squares cannot be identical."

    board = state_or_view.get("board") if isinstance(state_or_view, dict) else state_or_view.state["board"]
    r1, col1 = c1
    r2, col2 = c2

    # Verify whose turn it is
    players = state_or_view.get("players", [])
    p_white = players[0]["id"] if players else 0
    is_white_turn = (player_id == p_white)

    piece = board[r1][col1]
    if piece is None:
        return False, f"There is no piece on {from_str.upper()}."

    if is_white_turn and not is_white_piece(piece):
        return False, f"It is White's turn, but {from_str.upper()} holds a Black piece."
    if not is_white_turn and not is_black_piece(piece):
        return False, f"It is Black's turn, but {from_str.upper()} holds a White piece."

    valid, err = is_valid_piece_move(board, r1, col1, r2, col2, is_white_turn)
    if not valid:
        return False, err

    # Ensure move does not leave King in check
    temp_board = copy.deepcopy(board)
    temp_board[r2][col2] = temp_board[r1][col1]
    temp_board[r1][col1] = None
    if is_king_in_check(temp_board, is_white_turn):
        return False, "Illegal move: King would be in CHECK."

    return True, {"from": (r1, col1), "to": (r2, col2), "notation": f"{from_str}{to_str}"}


def apply_action(state, player_id, action_data):
    r1, c1 = action_data["from"]
    r2, c2 = action_data["to"]
    board = state["board"]
    piece = board[r1][c1]
    target = board[r2][c2]

    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    p_name = curr_p["name"]
    is_white = (curr_p["side"] == "White")

    # Handle capture
    captured_name = None
    if target is not None:
        captured_name = target
        if is_white:
            state["captured_white"].append(target)
        else:
            state["captured_black"].append(target)

    # Move piece
    board[r2][c2] = piece
    board[r1][c1] = None

    # Pawn Promotion (Auto-promote to Queen)
    promoted = False
    if piece == "P" and r2 == 0:
        board[r2][c2] = "Q"
        promoted = True
    elif piece == "p" and r2 == 7:
        board[r2][c2] = "q"
        promoted = True

    # Record notation
    notat = f"{to_coord(r1, c1)}➔{to_coord(r2, c2)}"
    if target:
        notat += f" (x{target.upper()})"
    if promoted:
        notat += "=Q"

    state["moves_history"].append(f"{curr_p['side'][:1]}: {notat}")

    # Check opponent check status
    opp_is_white = not is_white
    opp_in_check = is_king_in_check(board, opp_is_white)
    state["in_check"] = opp_in_check

    log_entry = f"♟ {p_name} ({curr_p['side']}) played {notat}."
    if opp_in_check:
        log_entry += " ⚠️ CHECK!"

    state["log"].append(log_entry)
    state["turn_index"] += 1

    # Check if king was captured (end game condition)
    opp_king = find_king(board, opp_is_white)
    if not opp_king:
        state["winner"] = [p_name]
        state["log"].append(f"🏆 {p_name} captures the King and WINS by checkmate!")

    return {"log": [log_entry]}


def is_over(state):
    return state["winner"] is not None


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
