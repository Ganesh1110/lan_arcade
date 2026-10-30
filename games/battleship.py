"""
Battleship Game Module.
2-Player Hidden Grid Strategy Game.
"""
import random
from config import paint
from utils.validation import parse_coordinate

game_id = "battleship"
game_name = "Battleship"
min_players = 2
max_players = 2

GRID_SIZE = 5
SHIPS_CONFIG = [
    ("Ship A", 3),
    ("Ship B", 2),
    ("Ship C", 2)
]


def place_ships_randomly():
    grid = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
    ship_locations = {}

    for name, length in SHIPS_CONFIG:
        placed = False
        while not placed:
            horizontal = random.choice([True, False])
            if horizontal:
                r = random.randint(0, GRID_SIZE - 1)
                c = random.randint(0, GRID_SIZE - length)
                cells = [(r, c + i) for i in range(length)]
            else:
                r = random.randint(0, GRID_SIZE - length)
                c = random.randint(0, GRID_SIZE - 1)
                cells = [(r + i, c) for i in range(length)]

            if all(grid[cr][cc] is None for cr, cc in cells):
                for cr, cc in cells:
                    grid[cr][cc] = name
                ship_locations[name] = set(cells)
                placed = True

    return grid, ship_locations


def create_state(player_sessions):
    players = []
    ships = {}
    ship_locs = {}
    shots = {}  # attacker_id -> {(r,c): hit_bool}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})

        grid, s_locs = place_ships_randomly()
        ships[pid] = grid
        ship_locs[pid] = s_locs
        shots[pid] = {}

    return {
        "players": players,
        "ships": ships,
        "ship_locs": ship_locs,
        "shots": shots,
        "turn_index": 0,
        "winner": None
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opponent = next((p for p in state["players"] if p["id"] != player_id), None)

    own_grid = state["ships"].get(player_id, [[None] * GRID_SIZE for _ in range(GRID_SIZE)])
    my_shots = state["shots"].get(player_id, {})

    opp_shots = {}
    if opponent:
        opp_shots = state["shots"].get(opponent["id"], {})

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opponent["name"] if opponent else "Opponent",
        "own_grid": own_grid,
        "my_shots": {f"{r},{c}": hit for (r, c), hit in my_shots.items()},
        "opp_shots": {f"{r},{c}": hit for (r, c), hit in opp_shots.items()},
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter target coordinate (e.g. C3, A1)"


def parse_action(state_or_view, player_id, raw_input):
    coord = parse_coordinate(raw_input, GRID_SIZE, GRID_SIZE)
    if coord is None:
        return False, f"Invalid coordinate '{raw_input}'. Enter A1–E5."

    r, c = coord

    if "shots" in state_or_view and isinstance(state_or_view["shots"], dict):
        shot_tuples = set(state_or_view["shots"].get(player_id, {}).keys())
    elif "my_shots" in state_or_view:
        my_shots = state_or_view.get("my_shots", {})
        if isinstance(my_shots, dict):
            shot_tuples = {
                (int(k.split(",")[0]), int(k.split(",")[1])) if isinstance(k, str) else k
                for k in my_shots.keys()
            }
        else:
            shot_tuples = set()
    else:
        shot_tuples = set()

    if (r, c) in shot_tuples:
        col_char = chr(ord('A') + c)
        return False, f"You already attacked {col_char}{r + 1}! Choose another coordinate."

    return True, (r, c)


def apply_action(state, player_id, coord):
    r, c = coord
    opponent = next(p for p in state["players"] if p["id"] != player_id)
    opp_id = opponent["id"]
    curr_player = next(p for p in state["players"] if p["id"] == player_id)

    opp_grid = state["ships"][opp_id]
    hit_ship = opp_grid[r][c]

    col_char = chr(ord('A') + c)
    target_str = f"{col_char}{r + 1}"

    if hit_ship is not None:
        is_hit = True
        log_msg = f"💥 {curr_player['name']} attacked {target_str} — HIT!"
    else:
        is_hit = False
        log_msg = f"💦 {curr_player['name']} attacked {target_str} — MISS."

    state["shots"][player_id][(r, c)] = is_hit

    # Check if all opponent ship cells are hit
    total_hits = sum(1 for hit in state["shots"][player_id].values() if hit)
    if total_hits >= 7:  # 3 + 2 + 2 = 7 total ship cells
        state["winner"] = [curr_player["name"]]
        log_msg += f" 🏆 {curr_player['name']} destroyed the enemy fleet and won!"

    state["turn_index"] += 1
    return {"log": [log_msg]}


def is_over(state):
    return state["winner"] is not None


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_grid_side_by_side(view):
    own_grid = view.get("own_grid", [[None] * GRID_SIZE for _ in range(GRID_SIZE)])
    my_shots_raw = view.get("my_shots", {})
    opp_shots_raw = view.get("opp_shots", {})

    def parse_shots(raw):
        res = {}
        for k, v in raw.items():
            if isinstance(k, str):
                parts = k.split(",")
                res[(int(parts[0]), int(parts[1]))] = v
            else:
                res[k] = v
        return res

    my_shots = parse_shots(my_shots_raw)
    opp_shots = parse_shots(opp_shots_raw)

    lines = []
    header = "      YOUR FLEET             TARGET HISTORY"
    col_sub = "    A B C D E               A B C D E"
    border  = "  +-----------+           +-----------+"

    lines.append(header)
    lines.append(col_sub)
    lines.append(border)

    for r in range(GRID_SIZE):
        # Your Fleet Grid (shows your ships + incoming opp_shots)
        left_cells = []
        for c in range(GRID_SIZE):
            if (r, c) in opp_shots:
                if opp_shots[(r, c)]:
                    left_cells.append(paint("X", "1;31"))  # Hit on your ship
                else:
                    left_cells.append(paint("O", "1;34"))  # Miss by opponent
            elif own_grid[r][c] is not None:
                left_cells.append(paint("S", "1;32"))     # Your ship
            else:
                left_cells.append(".")

        # Target Grid (shows your outgoing my_shots against opponent)
        right_cells = []
        for c in range(GRID_SIZE):
            if (r, c) in my_shots:
                if my_shots[(r, c)]:
                    right_cells.append(paint("X", "1;31"))  # Your hit
                else:
                    right_cells.append(paint("O", "1;34"))  # Your miss
            else:
                right_cells.append(".")

        left_str = " ".join(left_cells)
        right_str = " ".join(right_cells)
        lines.append(f"{r + 1} | {left_str} |         {r + 1} | {right_str} |")

    lines.append(border)
    return "\n".join(lines)


def render_dashboard(view):
    name = view.get("name", "Player")
    opp_name = view.get("opponent_name", "Opponent")
    turn_id = view.get("turn_id")
    my_id = view.get("player_id")
    log = view.get("log", [])

    out = [
        paint("=" * 50, "1;36"),
        paint("               B A T T L E S H I P", "1;36"),
        paint("=" * 50, "1;36"),
        "",
        f"  You: {name}   vs   Opponent: {opp_name}",
        "",
        render_grid_side_by_side(view),
        "",
        "  Legend: " + paint("S", "1;32") + " = Ship   " + paint("X", "1;31") + " = Hit   " + paint("O", "1;34") + " = Miss"
    ]

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
        parts.append(paint("  Game Over.", "1;33"))
    return "\n".join(parts)
