"""
Connect Four Game Module.
2-Player Strategy Board Game.
"""
from config import paint

game_id = "connect4"
game_name = "Connect Four"
min_players = 2
max_players = 2

ROWS = 6
COLS = 7


def create_state(player_sessions):
    players = []
    for s in player_sessions:
        if isinstance(s, dict):
            pid, name = s["id"], s["name"]
        else:
            pid, name = s.player_id, s.name
        players.append({"id": pid, "name": name})

    return {
        "board": [[None] * COLS for _ in range(ROWS)],
        "players": players,
        "symbols": {players[0]["id"]: "X", players[1]["id"]: "O"},
        "turn_index": 0,
        "winner": None,
        "winning_cells": [],
        "moves": 0
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "board": state["board"],
        "players": state["players"],
        "symbols": state["symbols"],
        "turn_id": current_player(state),
        "winner": state["winner"],
        "winning_cells": state["winning_cells"],
        "moves": state["moves"]
    }


def prompt_for(state_or_view, player_id):
    return "Choose column (1–7)"


def parse_action(state_or_view, player_id, raw_input):
    try:
        col = int(str(raw_input).strip())
    except (ValueError, TypeError):
        return False, "Enter a column number between 1 and 7."

    if not 1 <= col <= 7:
        return False, "Column number must be between 1 and 7."

    col_idx = col - 1
    board = state_or_view["board"]
    if board[0][col_idx] is not None:
        return False, f"Column {col} is full! Pick another column."

    return True, col_idx


def check_win(board, r, c, symbol):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        cells = [(r, c)]
        # Positive direction
        nr, nc = r + dr, c + dc
        while 0 <= nr < ROWS and 0 <= nc < COLS and board[nr][nc] == symbol:
            cells.append((nr, nc))
            nr += dr
            nc += dc

        # Negative direction
        nr, nc = r - dr, c - dc
        while 0 <= nr < ROWS and 0 <= nc < COLS and board[nr][nc] == symbol:
            cells.append((nr, nc))
            nr -= dr
            nc -= dc

        if len(cells) >= 4:
            return True, cells
    return False, []


def apply_action(state, player_id, col_idx):
    board = state["board"]
    symbol = state["symbols"][player_id]

    # Find lowest empty row in col_idx
    target_row = -1
    for r in range(ROWS - 1, -1, -1):
        if board[r][col_idx] is None:
            board[r][col_idx] = symbol
            target_row = r
            break

    state["moves"] += 1
    player = next(p for p in state["players"] if p["id"] == player_id)
    log_msg = f"{player['name']} ({symbol}) dropped token into column {col_idx + 1}"

    won, win_cells = check_win(board, target_row, col_idx, symbol)
    if won:
        state["winner"] = [player["name"]]
        state["winning_cells"] = win_cells
        log_msg += " and connected four!"

    state["turn_index"] += 1
    return {"log": [log_msg]}


def is_over(state):
    return state["winner"] is not None or state["moves"] >= ROWS * COLS


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    board = view.get("board", [[None] * COLS for _ in range(ROWS)])
    players = view.get("players", [])
    symbols = view.get("symbols", {})
    turn_id = view.get("turn_id")
    winning_cells = set(tuple(c) for c in view.get("winning_cells", []))
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("             C O N N E C T   F O U R", "1;36"),
        paint("=" * 48, "1;36"),
        ""
    ]

    # Render Board
    col_headers = "   " + "   ".join(str(c + 1) for c in range(COLS))
    out.append(col_headers)
    out.append("  +" + "---+" * COLS)

    for r in range(ROWS):
        row_str = [" |"]
        for c in range(COLS):
            val = board[r][c]
            if (r, c) in winning_cells:
                cell_str = paint(f" {val} ", "1;32")
            elif val == "X":
                cell_str = paint(" X ", "1;31")
            elif val == "O":
                cell_str = paint(" O ", "1;33")
            else:
                cell_str = " . "
            row_str.append(cell_str + "|")
        out.append("".join(row_str))
        out.append("  +" + "---+" * COLS)

    # Players info
    out.append("")
    for p in players:
        sym = symbols.get(str(p["id"]), symbols.get(p["id"], "?"))
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        c_sym = paint(f"[{sym}]", "1;31" if sym == "X" else "1;33")
        out.append(f"  {ptr} {p['name']:<20} {c_sym}")

    if log:
        out.append("")
        out.append("  Recent activity:")
        out.extend("   " + line for line in log)

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  🤝  GAME DRAW!  🤝", "1;33"))
    return "\n".join(parts)
