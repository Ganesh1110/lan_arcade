"""
Memory Match Game Module.
2–4 Player Card Flipping and Pair Matching Game.
"""
import copy
import random
from config import paint

game_id = "memory_match"
game_name = "Memory Match"
min_players = 2
max_players = 4

# Friendly, distinct card symbols (at least 12 distinct emojis)
CARD_SYMBOLS = [
    "🍎", "🍌", "🍇", "🍓", "🍒", "🍑", "🍍", "🥑",
    "🥕", "🌽", "🍉", "🍋", "🍄", "🥝", "🍔", "🍕"
]


def create_state(player_sessions):
    """
    Initialize a fresh Memory Match game state.
    Board size:
      - 2 players: 4x4 (16 cards = 8 pairs)
      - 3-4 players: 4x5 (20 cards = 10 pairs)
    """
    players = []
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})

    num_players = len(players)
    rows = 4
    cols = 4 if num_players <= 2 else 5
    num_pairs = (rows * cols) // 2

    # Pick random distinct symbols and double them
    chosen_symbols = random.sample(CARD_SYMBOLS, num_pairs)
    deck = chosen_symbols * 2
    random.shuffle(deck)

    # 4 rows x cols grid
    board = [deck[r * cols:(r + 1) * cols] for r in range(rows)]

    return {
        "players": players,
        "rows": rows,
        "cols": cols,
        "total_pairs": num_pairs,
        "pairs_remaining": num_pairs,
        "board": board,             # Full card faces: private to state, NEVER leaked in view_for
        "matched": set(),           # set of (r, c) tuples already matched
        "scores": {p["id"]: 0 for p in players},
        "turn_index": 0,
        "moves": 0,
        "last_reveal": None,        # dict with info on cards revealed during last turn
        "winner": None,
        "log": ["🧠 Memory Match started! Pick two face-down cards to find matching pairs."]
    }


def current_player(state):
    """Return player_id whose turn it currently is."""
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def prompt_for(state_or_view, player_id):
    """Prompt string for player action."""
    return "Pick two cards (e.g. A1 C3):"


def _parse_single_coord(token, rows, cols):
    """
    Parse a single card coordinate token such as 'A1', 'c3', '2B'.
    Returns ((r, c), err_msg).
    """
    t = str(token).strip().upper()
    if len(t) != 2:
        return None, f"Invalid coordinate format '{token}'. Use column letter and row number (e.g. A1)."

    c_char, r_char = t[0], t[1]
    # Allow row first or col first e.g. '1A' as well as 'A1'
    if t[0].isdigit() and t[1].isalpha():
        r_char, c_char = t[0], t[1]

    if not (c_char.isalpha() and r_char.isdigit()):
        return None, f"Invalid card coordinate '{token}'. Expected a column letter and row number (e.g. A1)."

    col = ord(c_char) - ord('A')
    row = int(r_char) - 1
    max_col_char = chr(ord('A') + cols - 1)

    if not (0 <= row < rows and 0 <= col < cols):
        return None, f"Coordinate '{token}' out of range. Columns are A–{max_col_char}, rows are 1–{rows}."

    return (row, col), None


def parse_action(state_or_view, player_id, raw_input):
    """
    Validate player action.
    Accepts: 'A1 C3', 'A1,C3', 'a1 c3', 'A1, C3'.
    Returns: (ok, action_or_error_str)
    """
    # 1. Turn check
    curr_turn = state_or_view.get("turn_id")
    if curr_turn is None and "players" in state_or_view and "turn_index" in state_or_view:
        curr_turn = current_player(state_or_view)

    if curr_turn is not None and curr_turn != player_id:
        return False, "It is not your turn."

    if raw_input is None:
        return False, "Please enter two card coordinates (e.g. A1 C3)."

    # 2. Token extraction
    raw = str(raw_input).strip().replace(",", " ")
    tokens = raw.split()
    if len(tokens) != 2:
        return False, "Please choose exactly two cards (e.g. 'A1 C3')."

    rows = state_or_view.get("rows", 4)
    cols = state_or_view.get("cols", 4)

    # 3. Parse coordinates
    c1, err1 = _parse_single_coord(tokens[0], rows, cols)
    if err1:
        return False, err1

    c2, err2 = _parse_single_coord(tokens[1], rows, cols)
    if err2:
        return False, err2

    # 4. Same card twice
    if c1 == c2:
        return False, "You must choose two different cards."

    # 5. Already matched check
    matched = state_or_view.get("matched", set())
    if isinstance(matched, list):
        # Could be list of [r, c] pairs from view
        matched_set = {(item[0], item[1]) for item in matched}
    else:
        matched_set = matched

    if c1 in matched_set:
        return False, f"Card {tokens[0].upper()} has already been matched!"

    if c2 in matched_set:
        return False, f"Card {tokens[1].upper()} has already been matched!"

    c1_str = f"{chr(ord('A') + c1[1])}{c1[0] + 1}"
    c2_str = f"{chr(ord('A') + c2[1])}{c2[0] + 1}"

    return True, {
        "card1": c1,
        "card2": c2,
        "c1_str": c1_str,
        "c2_str": c2_str
    }


def apply_action(state, player_id, action):
    """
    Apply action to state:
    - Reveal card1 and card2.
    - If match: award 1 point, cards stay matched, SAME player goes again.
    - If mismatch: cards flip back face-down, turn passes to next player.
    - Update last_reveal.
    """
    r1, c1 = action["card1"]
    r2, c2 = action["card2"]
    sym1 = state["board"][r1][c1]
    sym2 = state["board"][r2][c2]

    curr_p = next((p for p in state["players"] if p["id"] == player_id), None)
    p_name = curr_p["name"] if curr_p else "Player"
    c1_str = action.get("c1_str", f"{chr(ord('A') + c1)}{r1 + 1}")
    c2_str = action.get("c2_str", f"{chr(ord('A') + c2)}{r2 + 1}")

    matched = (sym1 == sym2)

    # Store last_reveal so both players can see what was flipped
    state["last_reveal"] = {
        "player_id": player_id,
        "player_name": p_name,
        "card1": {"row": r1, "col": c1, "coord": c1_str, "symbol": sym1},
        "card2": {"row": r2, "col": c2, "coord": c2_str, "symbol": sym2},
        "matched": matched
    }

    state["moves"] += 1

    if matched:
        state["matched"].add((r1, c1))
        state["matched"].add((r2, c2))
        state["scores"][player_id] = state["scores"].get(player_id, 0) + 1
        state["pairs_remaining"] = state["total_pairs"] - (len(state["matched"]) // 2)
        log_msg = f"{p_name} flipped {c1_str}={sym1} and {c2_str}={sym2} — MATCH! (+1 pair, goes again)"
        # Same player goes again (turn_index is NOT incremented)
    else:
        log_msg = f"{p_name} flipped {c1_str}={sym1} and {c2_str}={sym2} — no match."
        state["turn_index"] += 1

    if is_over(state):
        winners = get_winner(state)
        state["winner"] = winners
        if len(winners) == 1:
            log_msg += f" 🎉 All pairs found! {winners[0]} wins!"
        else:
            log_msg += f" 🎉 All pairs found! Tie between {', '.join(winners)}!"

    return {"log": [log_msg]}


def skip_player(state, player_id):
    """Pass turn on timeout or surrender without scoring or flipping."""
    if current_player(state) == player_id:
        state["turn_index"] += 1


def is_over(state):
    """Game is over when all card pairs have been matched."""
    return len(state["matched"]) >= state["rows"] * state["cols"]


def get_winner(state):
    """
    Return list of winner names (player with the most pairs).
    In case of ties, returns all tied players.
    """
    if not is_over(state):
        return []
    scores = state["scores"]
    if not scores:
        return []
    max_score = max(scores.values())
    return [p["name"] for p in state["players"] if scores.get(p["id"], 0) == max_score]


def view_for(state, player_id):
    """
    Build private view payload for a player.
    CRITICAL: Never includes card faces for face-down cards!
    Only matched cards and the 2 cards revealed in last_reveal are sent.
    """
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    rows = state["rows"]
    cols = state["cols"]
    matched = state["matched"]

    # Face-down cards are strictly None
    board_view = [[None for _ in range(cols)] for _ in range(rows)]
    for r, c in matched:
        board_view[r][c] = state["board"][r][c]

    # Convert matched to list of [r, c] for clean JSON serialization
    matched_list = sorted([[r, c] for r, c in matched])

    scores_dict = {p["id"]: state["scores"].get(p["id"], 0) for p in state["players"]}

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "rows": rows,
        "cols": cols,
        "board": board_view,
        "matched": matched_list,
        "scores": scores_dict,
        "total_pairs": state["total_pairs"],
        "pairs_remaining": state["pairs_remaining"],
        "players": state["players"],
        "turn_id": current_player(state),
        "last_reveal": copy.deepcopy(state.get("last_reveal")),
        "winner": get_winner(state) if is_over(state) else None
    }


def render_dashboard(view):
    """Render Memory Match game dashboard for terminal."""
    rows = view.get("rows", 4)
    cols = view.get("cols", 4)
    board = view.get("board", [[None] * cols for _ in range(rows)])
    matched_raw = view.get("matched", [])
    matched_set = {(item[0], item[1]) for item in matched_raw}
    scores = view.get("scores", {})
    players = view.get("players", [])
    turn_id = view.get("turn_id")
    pairs_left = view.get("pairs_remaining", 0)
    total_pairs = view.get("total_pairs", (rows * cols) // 2)
    last_reveal = view.get("last_reveal")
    log = view.get("log", [])

    out = [
        paint("=" * 56, "1;36"),
        paint("                 M E M O R Y   M A T C H", "1;36"),
        paint("=" * 56, "1;36"),
        ""
    ]

    # Column headers: A, B, C, D (and E)
    col_letters = [chr(ord('A') + c) for c in range(cols)]
    header_str = "        " + "      ".join(col_letters)
    out.append(paint(header_str, "1;33"))

    top_border = "     ┌" + "──────┬" * (cols - 1) + "──────┐"
    mid_border = "     ├" + "──────┼" * (cols - 1) + "──────┤"
    bot_border = "     └" + "──────┴" * (cols - 1) + "──────┘"

    out.append(paint(top_border, "2;37"))

    # Recent reveal positions for temporary peek highlighting
    recent_reveal_map = {}
    if last_reveal:
        c1 = last_reveal.get("card1", {})
        c2 = last_reveal.get("card2", {})
        if "row" in c1 and "col" in c1 and "symbol" in c1:
            recent_reveal_map[(c1["row"], c1["col"])] = c1["symbol"]
        if "row" in c2 and "col" in c2 and "symbol" in c2:
            recent_reveal_map[(c2["row"], c2["col"])] = c2["symbol"]

    for r in range(rows):
        row_num = paint(f"  {r + 1}  ", "1;33")
        cells = []
        for c in range(cols):
            if (r, c) in matched_set and board[r][c] is not None:
                # Already matched pair: display emoji
                sym = board[r][c]
                cells.append(paint(f"  {sym}  ", "1;32"))
            elif (r, c) in recent_reveal_map:
                # Revealed on previous turn (peek before face down)
                sym = recent_reveal_map[(r, c)]
                is_match = last_reveal.get("matched", False)
                color = "1;32;40" if is_match else "1;33;40"
                cells.append(paint(f"  {sym}  ", color))
            else:
                # Face-down card
                cells.append(paint("  ▒▒  ", "2;37"))

        row_line = row_num + paint("│", "2;37") + paint("│", "2;37").join(cells) + paint("│", "2;37")
        out.append(row_line)
        if r < rows - 1:
            out.append(paint(mid_border, "2;37"))
        else:
            out.append(paint(bot_border, "2;37"))

    out.append("")

    # Scores and status line
    score_parts = []
    for p in players:
        sc = scores.get(p["id"], scores.get(str(p["id"]), 0))
        is_turn = (p["id"] == turn_id)
        ptr = paint("▶ ", "1;32") if is_turn else "  "
        score_parts.append(f"{ptr}{p['name']}: {paint(sc, '1;33')} pair{'s' if sc != 1 else ''}")

    out.append("  " + "  |  ".join(score_parts))
    out.append(paint(f"  Pairs Remaining: {pairs_left} / {total_pairs}", "2"))

    # Last reveal line
    if last_reveal:
        p_name = last_reveal.get("player_name", "Player")
        c1 = last_reveal.get("card1", {})
        c2 = last_reveal.get("card2", {})
        c1_txt = f"{c1.get('coord', '?')}={c1.get('symbol', '?')}"
        c2_txt = f"{c2.get('coord', '?')}={c2.get('symbol', '?')}"
        if last_reveal.get("matched"):
            result_txt = paint("MATCH! 🎉 (plays again)", "1;32")
        else:
            result_txt = paint("no match.", "1;31")
        out.append(paint(f"  👀 Last Turn: {p_name} flipped {c1_txt} and {c2_txt} — {result_txt}", "1;33"))

    if log:
        out.append("")
        out.append("  Recent Activity:")
        for line in log[-3:]:
            out.append("   " + line)

    return "\n".join(out)


def render_final(view, message, winners):
    """Render game over final screen."""
    parts = [render_dashboard(view), ""]
    if winners:
        if len(winners) == 1:
            parts.append(paint(f"  🏆  VICTORY! {winners[0]} WINS MEMORY MATCH!  🏆", "1;32"))
        else:
            parts.append(paint(f"  🤝  TIE GAME! Winners: {', '.join(winners)}!  🤝", "1;33"))
    else:
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
