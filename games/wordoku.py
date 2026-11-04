"""
Wordoku (6x6 Mini Sudoku) Game Module.
2-Player Competitive Deductive Grid Game.
"""
import re
import random
from config import paint

game_id = "wordoku"
game_name = "Wordoku (Mini Sudoku)"
min_players = 2
max_players = 2

GRID_SIZE = 6
VALID_LETTERS = {"A", "B", "C", "D", "E", "F"}

PUZZLES = [
    {
        "solution": [
            ["A", "B", "C", "D", "E", "F"],
            ["D", "E", "F", "A", "B", "C"],
            ["B", "C", "A", "E", "F", "D"],
            ["E", "F", "D", "B", "C", "A"],
            ["C", "A", "B", "F", "D", "E"],
            ["F", "D", "E", "C", "A", "B"]
        ],
        "initial": [
            ["A", None, "C", None, "E", None],
            [None, "E", None, "A", None, "C"],
            ["B", "C", None, "E", None, "D"],
            ["E", None, "D", None, None, "A"],
            [None, "A", None, "F", None, "E"],
            [None, "D", None, "C", None, "B"]
        ]
    },
    {
        "solution": [
            ["F", "E", "D", "C", "B", "A"],
            ["C", "B", "A", "F", "E", "D"],
            ["E", "D", "F", "B", "A", "C"],
            ["B", "A", "C", "E", "D", "F"],
            ["D", "F", "E", "A", "C", "B"],
            ["A", "C", "B", "D", "F", "E"]
        ],
        "initial": [
            ["F", "E", None, "C", None, "A"],
            ["C", None, "A", None, "E", None],
            ["E", "D", None, None, "A", "C"],
            ["B", "A", None, None, "D", None],
            [None, "F", None, "A", None, "B"],
            ["A", None, "B", None, "F", "E"]
        ]
    },
    {
        "solution": [
            ["B", "C", "A", "E", "F", "D"],
            ["E", "F", "D", "B", "C", "A"],
            ["A", "B", "C", "D", "E", "F"],
            ["D", "E", "F", "A", "B", "C"],
            ["F", "D", "E", "C", "A", "B"],
            ["C", "A", "B", "F", "D", "E"]
        ],
        "initial": [
            ["B", None, "A", None, "F", None],
            [None, "F", None, "B", None, "A"],
            ["A", "B", None, "D", None, "F"],
            ["D", None, "F", None, None, "C"],
            [None, "D", None, "C", None, "B"],
            [None, "A", None, "F", None, "E"]
        ]
    }
]

# Legacy fallbacks
SOLUTION = PUZZLES[0]["solution"]
INITIAL_PUZZLE = PUZZLES[0]["initial"]


def is_valid_placement(grid, r, c, val):
    for i in range(GRID_SIZE):
        if grid[r][i] == val or grid[i][c] == val:
            return False
    br = (r // 2) * 2
    bc = (c // 3) * 3
    for dr in range(2):
        for dc in range(3):
            if grid[br + dr][bc + dc] == val:
                return False
    return True


def has_solution(grid):
    """Backtracking solver verifying if grid has at least one valid completion."""
    def backtrack(g):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if g[r][c] is None:
                    for v in ["A", "B", "C", "D", "E", "F"]:
                        if is_valid_placement(g, r, c, v):
                            g[r][c] = v
                            if backtrack(g):
                                return True
                            g[r][c] = None
                    return False
        return True
    return backtrack([row[:] for row in grid])


def create_state(player_sessions):
    players = []
    scores = {}
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        scores[pid] = 0

    puzzle = random.choice(PUZZLES)
    grid = [row[:] for row in puzzle["initial"]]
    empty_cnt = sum(1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid[r][c] is None)

    return {
        "players": players,
        "scores": scores,
        "grid": grid,
        "puzzle": puzzle,
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
        "players": state["players"],
        "grid": state["grid"],
        "scores": state["scores"],
        "empty_count": state["empty_count"],
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter placement (e.g. 'R1 C2 B' or '1 2 B')"


def parse_action(state_or_view, player_id, raw_input):
    raw = str(raw_input).strip().upper()
    # Match inputs like: 'R1 C2 B', '1 2 C', 'R1C2 C', '1, 2, C', 'r1 c2 c'
    m = re.match(r'^(?:R\s*)?([1-6])[\s,]+(?:C\s*)?([1-6])[\s,]+([A-F])$', raw)
    if not m:
        m = re.match(r'^R([1-6])\s*C([1-6])[\s,]+([A-F])$', raw)
    if not m:
        return False, "Format: 'R<row> C<col> <letter>' (e.g. 'R1 C2 B' or '1 2 C')."

    r = int(m.group(1)) - 1
    c = int(m.group(2)) - 1
    val = m.group(3)

    grid = state_or_view.get("grid", [])
    if grid and grid[r][c] is not None:
        return False, f"Cell R{r + 1} C{c + 1} is already filled!"

    return True, {"r": r, "c": c, "val": val}


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    r, c, val = action["r"], action["c"], action["val"]

    puzzle = state.get("puzzle", PUZZLES[0])
    expected_val = puzzle["solution"][r][c]
    log_entries = []

    # Valid if matches solution or is mathematically valid with a full solvable completion
    is_correct = (val == expected_val)
    if not is_correct and is_valid_placement(state["grid"], r, c, val):
        test_g = [row[:] for row in state["grid"]]
        test_g[r][c] = val
        if has_solution(test_g):
            is_correct = True

    if is_correct:
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
    raw_scores = view.get("scores", {})
    scores = {int(k): v for k, v in raw_scores.items()} if isinstance(raw_scores, dict) else {}
    players = view.get("players", [])
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

    col_hdr = "       C1  C2  C3   C4  C5  C6"
    out.append(paint(col_hdr, "1;36"))

    top_b = "   ╔═══╤═══╤═══╦═══╤═══╤═══╗"
    mid_l = "   ╟───┼───┼───╫───┼───┼───╢"
    mid_h = "   ╠═══╪═══╪═══╬═══╪═══╪═══╣"
    bot_b = "   ╚═══╧═══╧═══╩═══╧═══╧═══╝"

    out.append(top_b)

    for r in range(GRID_SIZE):
        row_cells = []
        for c in range(GRID_SIZE):
            v = grid[r][c]
            cell = paint(f" {v} ", "1;32") if v else paint(" · ", "2")
            row_cells.append(cell)

        # Split into 2 blocks of 3
        part1 = "│".join(row_cells[:3])
        part2 = "│".join(row_cells[3:])
        out.append(f"R{r + 1} ║{part1}║{part2}║")

        if r == 1 or r == 3:
            out.append(mid_h)
        elif r == 5:
            out.append(bot_b)
        else:
            out.append(mid_l)

    out.append("")
    out.append("  SCOREBOARD:")
    for p in players:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        sc = scores.get(p["id"], 0)
        out.append(f"   {ptr} {p['name']:<20} Score: {sc} pts")

    if log:
        out.append("")
        out.append("  Recent activity:")
        out.extend("   " + line for line in log[-4:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
