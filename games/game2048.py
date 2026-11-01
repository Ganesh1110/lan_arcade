"""
2048 Versus Game Module.
2-Player Competitive Tile Merging Race.
"""
import random
from config import paint

game_id = "game2048"
game_name = "2048 Versus"
min_players = 2
max_players = 2

GRID_SIZE = 4


def spawn_tile(grid):
    empty = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid[r][c] == 0]
    if empty:
        r, c = random.choice(empty)
        grid[r][c] = 2 if random.random() < 0.9 else 4


def create_initial_grid():
    grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    spawn_tile(grid)
    spawn_tile(grid)
    return grid


def create_state(player_sessions):
    players = []
    boards = {}
    scores = {}
    max_tiles = {}
    moves = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        boards[pid] = create_initial_grid()
        scores[pid] = 0
        max_tiles[pid] = max(max(row) for row in boards[pid])
        moves[pid] = 0

    return {
        "players": players,
        "boards": boards,
        "scores": scores,
        "max_tiles": max_tiles,
        "moves": moves,
        "turn_index": 0,
        "winner": None
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    my_board = state["boards"].get(player_id, [[0] * GRID_SIZE for _ in range(GRID_SIZE)])
    opp_board = state["boards"].get(opp["id"], [[0] * GRID_SIZE for _ in range(GRID_SIZE)]) if opp else []

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "my_board": my_board,
        "my_score": state["scores"].get(player_id, 0),
        "my_max": state["max_tiles"].get(player_id, 2),
        "opp_score": state["scores"].get(opp["id"], 0) if opp else 0,
        "opp_max": state["max_tiles"].get(opp["id"], 2) if opp else 2,
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Shift direction: 'W' (Up), 'A' (Left), 'S' (Down), 'D' (Right)"


def parse_action(state_or_view, player_id, raw_input):
    move = str(raw_input).strip().upper()
    if move in {"W", "A", "S", "D"}:
        return True, move
    return False, "Direction must be W (Up), A (Left), S (Down), or D (Right)."


def slide_and_merge_line(line):
    # Slide
    non_zero = [v for v in line if v != 0]
    merged = []
    score_gain = 0
    skip = False

    for i in range(len(non_zero)):
        if skip:
            skip = False
            continue
        if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
            val = non_zero[i] * 2
            merged.append(val)
            score_gain += val
            skip = True
        else:
            merged.append(non_zero[i])

    merged.extend([0] * (GRID_SIZE - len(merged)))
    return merged, score_gain


def move_grid(grid, direction):
    new_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    total_score_gain = 0

    if direction == "A":  # Left
        for r in range(GRID_SIZE):
            new_grid[r], gain = slide_and_merge_line(grid[r])
            total_score_gain += gain
    elif direction == "D":  # Right
        for r in range(GRID_SIZE):
            line = list(reversed(grid[r]))
            m_line, gain = slide_and_merge_line(line)
            new_grid[r] = list(reversed(m_line))
            total_score_gain += gain
    elif direction == "W":  # Up
        for c in range(GRID_SIZE):
            col = [grid[r][c] for r in range(GRID_SIZE)]
            m_col, gain = slide_and_merge_line(col)
            for r in range(GRID_SIZE):
                new_grid[r][c] = m_col[r]
            total_score_gain += gain
    elif direction == "S":  # Down
        for c in range(GRID_SIZE):
            col = [grid[r][c] for r in range(GRID_SIZE)]
            col = list(reversed(col))
            m_col, gain = slide_and_merge_line(col)
            m_col = list(reversed(m_col))
            for r in range(GRID_SIZE):
                new_grid[r][c] = m_col[r]
            total_score_gain += gain

    changed = (new_grid != grid)
    return new_grid, changed, total_score_gain


def apply_action(state, player_id, direction):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    grid = state["boards"][player_id]

    new_grid, changed, gain = move_grid(grid, direction)
    log_entries = []

    if changed:
        spawn_tile(new_grid)
        state["boards"][player_id] = new_grid
        state["scores"][player_id] += gain
        state["moves"][player_id] += 1
        max_t = max(max(row) for row in new_grid)
        state["max_tiles"][player_id] = max_t

        dir_names = {"W": "UP", "A": "LEFT", "S": "DOWN", "D": "RIGHT"}
        log_entries.append(f"🎮 {curr_p['name']} shifted {dir_names[direction]} (Score: {state['scores'][player_id]}, Max Tile: {max_t})")

        # Win condition: 2048 tile reached!
        if max_t >= 2048:
            state["winner"] = [curr_p["name"]]
            log_entries.append(f"🏆 {curr_p['name']} REACHED THE 2048 TILE AND WINS THE RACE!")
    else:
        log_entries.append(f"{curr_p['name']} shifted {direction} (No tiles merged/moved).")

    state["turn_index"] += 1
    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or any(t >= 2048 for t in state["max_tiles"].values())


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    name = view.get("name", "Player")
    opp_name = view.get("opponent_name", "Opponent")
    my_board = view.get("my_board", [[0] * GRID_SIZE for _ in range(GRID_SIZE)])
    my_score = view.get("my_score", 0)
    my_max = view.get("my_max", 2)
    opp_score = view.get("opp_score", 0)
    opp_max = view.get("opp_max", 2)
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("               2 0 4 8   V E R S U S", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        f"  You ({name}): Score {my_score} | Max {my_max}   vs   {opp_name}: Score {opp_score} | Max {opp_max}",
        "",
        "  YOUR 2048 BOARD:"
    ]

    border = "  +" + "------+" * GRID_SIZE
    out.append(border)
    for r in range(GRID_SIZE):
        row_str = ["  |"]
        for c in range(GRID_SIZE):
            v = my_board[r][c]
            if v == 0:
                cell = "  .   "
            else:
                cell = f"{v:^6}"
                if v >= 1024:
                    cell = paint(cell, "1;32")
                elif v >= 128:
                    cell = paint(cell, "1;33")
                elif v >= 16:
                    cell = paint(cell, "1;35")
                else:
                    cell = paint(cell, "1;36")
            row_str.append(cell + "|")
        out.append("".join(row_str))
        out.append(border)

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
