"""
Tic-Tac-Toe Game Module.
2-Player Classic 3x3 Grid Game.
"""
from config import paint

game_id = "tic_tac_toe"
game_name = "Tic-Tac-Toe"
min_players = 2
max_players = 2


def create_state(player_sessions):
    players = []
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})

    return {
        "board": [None] * 9,
        "players": players,
        "symbols": {players[0]["id"]: "X", players[1]["id"]: "O"},
        "turn_index": 0,
        "moves": 0,
        "winner": None
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
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Choose position (1–9)"


def parse_action(state_or_view, player_id, raw_input):
    try:
        cell = int(str(raw_input).strip())
    except (ValueError, TypeError):
        return False, "Enter a cell number between 1 and 9."

    if not 1 <= cell <= 9:
        return False, "Cell number must be between 1 and 9."

    idx = cell - 1
    board = state_or_view["board"]
    if board[idx] is not None:
        return False, f"Cell {cell} is already taken!"

    return True, idx


def check_win(board, symbol):
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
        (0, 4, 8), (2, 4, 6)               # Diagonals
    ]
    for a, b, c in lines:
        if board[a] == symbol and board[b] == symbol and board[c] == symbol:
            return True
    return False


def apply_action(state, player_id, cell_idx):
    symbol = state["symbols"][player_id]
    state["board"][cell_idx] = symbol
    state["moves"] += 1

    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    log_msg = f"{curr_p['name']} placed {symbol} at position {cell_idx + 1}"

    if check_win(state["board"], symbol):
        state["winner"] = [curr_p["name"]]
        log_msg += " and won!"

    state["turn_index"] += 1
    return {"log": [log_msg]}


def is_over(state):
    return state["winner"] is not None or state["moves"] >= 9


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    board = view.get("board", [None] * 9)
    players = view.get("players", [])
    symbols = view.get("symbols", {})
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("           T I C - T A C - T O E", "1;36"),
        paint("=" * 48, "1;36"),
        ""
    ]

    def cell_char(i):
        v = board[i]
        if v == "X":
            return paint(" X ", "1;31")
        if v == "O":
            return paint(" O ", "1;33")
        return paint(f" {i + 1} ", "2")

    grid_str = [
        f"       {cell_char(0)} | {cell_char(1)} | {cell_char(2)}",
        "      ----+-----+----",
        f"       {cell_char(3)} | {cell_char(4)} | {cell_char(5)}",
        "      ----+-----+----",
        f"       {cell_char(6)} | {cell_char(7)} | {cell_char(8)}"
    ]
    out.extend(grid_str)

    out.append("")
    for p in players:
        sym = symbols.get(p["id"], "?")
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        out.append(f"  {ptr} {p['name']:<20} [{sym}]")

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
