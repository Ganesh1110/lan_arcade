"""
2048 Versus Game Module.
2-Player Competitive Tile Merging Race with Side-by-Side Dual Boards.
"""
import random
from config import paint

game_id = "game2048"
game_name = "2048 Versus"
min_players = 2
max_players = 2

GRID_SIZE = 4
WIN_TILE = 2048


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


def can_move(grid):
    """Check if any legal slide moves exist on the board."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] == 0:
                return True
            # Right neighbor
            if c + 1 < GRID_SIZE and grid[r][c] == grid[r][c + 1]:
                return True
            # Bottom neighbor
            if r + 1 < GRID_SIZE and grid[r][c] == grid[r + 1][c]:
                return True
    return False


def create_state(player_sessions):
    players = []
    boards = {}
    scores = {}
    max_tiles = {}
    moves = {}
    locked_out = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        boards[pid] = create_initial_grid()
        scores[pid] = 0
        max_tiles[pid] = max(max(row) for row in boards[pid])
        moves[pid] = 0
        locked_out[pid] = False

    return {
        "players": players,
        "boards": boards,
        "scores": scores,
        "max_tiles": max_tiles,
        "moves": moves,
        "locked_out": locked_out,
        "turn_index": 0,
        "winner": None
    }


def current_player(state):
    players = state["players"]
    # If one player is locked out, give turn to remaining unlocked player
    for offset in range(len(players)):
        idx = (state["turn_index"] + offset) % len(players)
        pid = players[idx]["id"]
        if not state["locked_out"].get(pid, False):
            return pid
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
        "opp_board": opp_board,
        "my_score": state["scores"].get(player_id, 0),
        "my_max": state["max_tiles"].get(player_id, 2),
        "opp_score": state["scores"].get(opp["id"], 0) if opp else 0,
        "opp_max": state["max_tiles"].get(opp["id"], 2) if opp else 2,
        "my_locked": state["locked_out"].get(player_id, False),
        "opp_locked": state["locked_out"].get(opp["id"], False) if opp else False,
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
        log_entries.append(
            f"🎮 {curr_p['name']} shifted {dir_names[direction]} (Score: {state['scores'][player_id]}, Max: {max_t})"
        )

        # Win condition: 2048 tile reached!
        if max_t >= WIN_TILE:
            state["winner"] = [curr_p["name"]]
            log_entries.append(f"🏆 {curr_p['name']} REACHED THE {WIN_TILE} TILE AND WINS THE RACE!")
    else:
        log_entries.append(f"{curr_p['name']} shifted {direction} (No tiles moved).")

    # Check if this player can make any more moves
    active_grid = state["boards"][player_id]
    if not can_move(active_grid):
        state["locked_out"][player_id] = True
        log_entries.append(f"🔒 {curr_p['name']}'s board is locked out! No legal moves remaining.")

    # Check if all players are locked out
    if all(state["locked_out"].values()):
        max_score = max(state["scores"].values())
        winners = [p["name"] for p in state["players"] if state["scores"][p["id"]] == max_score]
        state["winner"] = winners
        log_entries.append(f"🏁 All boards locked out! Game over! Winner by score: {', '.join(winners)}")

    state["turn_index"] += 1
    return {"log": log_entries}


def is_over(state):
    if state["winner"] is not None:
        return True
    if any(t >= WIN_TILE for t in state["max_tiles"].values()):
        return True
    if all(state["locked_out"].values()):
        return True
    return False


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    if all(state["locked_out"].values()) or is_over(state):
        max_score = max(state["scores"].values())
        return [p["name"] for p in state["players"] if state["scores"][p["id"]] == max_score]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def _format_cell(v):
    if v == 0:
        return "  .  "
    cell = f"{v:^5}"
    if v >= 1024:
        return paint(cell, "1;32")
    elif v >= 128:
        return paint(cell, "1;33")
    elif v >= 16:
        return paint(cell, "1;35")
    else:
        return paint(cell, "1;36")


def render_dashboard(view):
    name = view.get("name", "Player")
    opp_name = view.get("opponent_name", "Opponent")
    my_board = view.get("my_board", [[0] * GRID_SIZE for _ in range(GRID_SIZE)])
    opp_board = view.get("opp_board", [[0] * GRID_SIZE for _ in range(GRID_SIZE)])
    my_score = view.get("my_score", 0)
    my_max = view.get("my_max", 2)
    opp_score = view.get("opp_score", 0)
    opp_max = view.get("opp_max", 2)
    my_locked = view.get("my_locked", False)
    opp_locked = view.get("opp_locked", False)
    log = view.get("log", [])

    out = [
        paint("=" * 60, "1;36"),
        paint("                  2 0 4 8   V E R S U S", "1;36"),
        paint("=" * 60, "1;36"),
        ""
    ]

    left_header = f"YOUR BOARD ({name})" + (" [LOCKED]" if my_locked else "")
    right_header = f"OPPONENT ({opp_name})" + (" [LOCKED]" if opp_locked else "")
    out.append(f"  {left_header:<27}        {right_header:<27}")
    out.append(f"  Score: {my_score:<5} Max: {my_max:<5}              Score: {opp_score:<5} Max: {opp_max:<5}")

    border = "  +" + "-----+-----+-----+-----+"
    out.append(f"{border}      {border.strip()}")

    for r in range(GRID_SIZE):
        # My row
        my_cells = [_format_cell(my_board[r][c]) for c in range(GRID_SIZE)]
        my_row_str = "  |" + "|".join(my_cells) + "|"

        # Opponent row
        if opp_board and len(opp_board) > r:
            opp_cells = [_format_cell(opp_board[r][c]) for c in range(GRID_SIZE)]
            opp_row_str = "  |" + "|".join(opp_cells) + "|"
        else:
            opp_row_str = "  |  .  |  .  |  .  |  .  |"

        out.append(f"{my_row_str}    {opp_row_str.strip()}")
        out.append(f"{border}      {border.strip()}")

    if log:
        out.append("")
        out.append("  Recent activity:")
        out.extend("   " + line for line in log[-5:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
