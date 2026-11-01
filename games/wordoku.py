"""
Wordoku (6x6 Mini Sudoku) Game Module.
2-Player Competitive Deductive Grid Game.
"""
from config import paint

game_id = "wordoku"
game_name = "Wordoku (Mini Sudoku)"
min_players = 2
max_players = 2

GRID_SIZE = 6
VALID_LETTERS = {"A", "B", "C", "D", "E", "F"}

SOLUTION = [
    ["A", "B", "C", "D", "E", "F"],
    ["D", "E", "F", "A", "B", "C"],
    ["B", "C", "A", "E", "F", "D"],
    ["E", "F", "D", "B", "C", "A"],
    ["C", "A", "B", "F", "D", "E"],
    ["F", "D", "E", "C", "A", "B"]
]

# Initial puzzle (None means empty)
INITIAL_PUZZLE = [
    ["A", None, "C", None, "E", None],
    [None, "E", None, "A", None, "C"],
    ["B", None, None, "E", None, "D"],
    ["E", None, "D", None, None, "A"],
    [None, "A", None, "F", None, "E"],
    [None, "D", None, "C", None, "B"]
]


def create_state(player_sessions):
    players = []
    scores = {}
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        scores[pid] = 0

    grid = [row[:] for row in INITIAL_PUZZLE]
    empty_cnt = sum(1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid[r][c] is None)

    return {
        "players": players,
        "scores": scores,
        "grid": grid,
        "empty_count": empty_cnt,
        "turn_index": 0,
        "winner": None
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
        "opponent_name": opp["name"] if opp else "Opponent",
        "grid": state["grid"],
        "scores": state["scores"],
        "empty_count": state["empty_count"],
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter placement (e.g. 'R1 C2 B' or '1 2 B')"


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip().upper().replace("R", "").replace("C", "")
    parts = text.split()
    if len(parts) != 3:
        return False, "Format: 'R<row> C<col> <letter>' (e.g. 'R1 C2 B')."

    try:
        r = int(parts[0]) - 1
        c = int(parts[1]) - 1
    except ValueError:
        return False, "Row and Column must be numbers between 1 and 6."

    val = parts[2]
    if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
        return False, "Row and Column must be between 1 and 6."

    if val not in VALID_LETTERS:
        return False, "Letter value must be A, B, C, D, E, or F."

    grid = state_or_view.get("grid", [])
    if grid and grid[r][c] is not None:
        return False, f"Cell R{r + 1} C{c + 1} is already filled!"

    return True, {"r": r, "c": c, "val": val}


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    r, c, val = action["r"], action["c"], action["val"]
    expected_val = SOLUTION[r][c]
    log_entries = []

    if val == expected_val:
        state["grid"][r][c] = val
        state["scores"][player_id] += 10
        state["empty_count"] -= 1
        log_entries.append(f"✨ {curr_p['name']} correctly placed '{val}' at R{r + 1} C{c + 1} (+10 pts)!")
    else:
        state["scores"][player_id] = max(0, state["scores"][player_id] - 5)
        log_entries.append(f"❌ {curr_p['name']} placed '{val}' at R{r + 1} C{c + 1} — WRONG! (-5 pts penalty)")

    if state["empty_count"] == 0:
        max_s = max(state["scores"].values())
        state["winner"] = [p["name"] for p in state["players"] if state["scores"][p["id"]] == max_s]
        log_entries.append("🎉 Wordoku grid completed!")

    state["turn_index"] += 1
    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or state["empty_count"] == 0


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    max_s = max(state["scores"].values()) if state["scores"] else 0
    return [p["name"] for p in state["players"] if state["scores"][p["id"]] == max_s]


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    grid = view.get("grid", [[None] * GRID_SIZE for _ in range(GRID_SIZE)])
    scores = view.get("scores", {})
    empty_cnt = view.get("empty_count", 0)
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("             W O R D O K U   (6x6)", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        f"  Empty Cells Remaining: {empty_cnt}",
        ""
    ]

    col_hdr = "    " + "   ".join(f"C{c + 1}" for c in range(GRID_SIZE))
    out.append(col_hdr)
    border = "   +" + "---+" * GRID_SIZE
    out.append(border)

    for r in range(GRID_SIZE):
        row_str = [f"R{r + 1} |"]
        for c in range(GRID_SIZE):
            v = grid[r][c]
            cell = paint(f" {v} ", "1;32") if v else " . "
            row_str.append(cell + "|")
        out.append("".join(row_str))
        out.append(border)

    out.append("")
    out.append("  SCOREBOARD:")
    for p in view.get("players", []):
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        sc = scores.get(p["id"], 0)
        out.append(f"   {ptr} {p['name']:<20} Score: {sc} pts")

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
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
