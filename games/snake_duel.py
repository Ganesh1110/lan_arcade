"""
Snake Duel / Tron Lightcycles Game Module.
2-Player Competitive Grid Duel with Solid Light Trails, Energy Pellets, and Collision Physics.
"""
import random
from config import paint

game_id = "snake_duel"
game_name = "Snake Duel"
min_players = 2
max_players = 2

ARENA_WIDTH = 30
ARENA_HEIGHT = 14

DIRS = {
    "W": (0, -1),   # Up
    "S": (0, 1),    # Down
    "A": (-1, 0),   # Left
    "D": (1, 0),    # Right
}

HEAD_ICONS = {
    (0, -1): "▲",
    (0, 1): "▼",
    (-1, 0): "◄",
    (1, 0): "►"
}


def spawn_pellet(trails, p1_pos, p2_pos):
    """Find empty arena cell for energy pellet."""
    occupied = set(trails.get(0, [])) | set(trails.get(1, [])) | {p1_pos, p2_pos}
    candidates = [
        (x, y) for x in range(1, ARENA_WIDTH - 1)
        for y in range(1, ARENA_HEIGHT - 1)
        if (x, y) not in occupied
    ]
    return random.choice(candidates) if candidates else None


def create_state(player_sessions):
    players = []
    positions = {}
    directions = {}
    trails = {}
    alive = {}
    lengths = {}

    p1_start = (5, ARENA_HEIGHT // 2)
    p2_start = (ARENA_WIDTH - 6, ARENA_HEIGHT // 2)

    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        color = "1;33" if idx == 0 else "1;36"
        token = f"P{idx + 1}"
        players.append({"id": pid, "name": name, "color": color, "token": token})

        pos = p1_start if idx == 0 else p2_start
        d = (1, 0) if idx == 0 else (-1, 0)  # P1 faces Right, P2 faces Left

        positions[pid] = pos
        directions[pid] = d
        trails[pid] = [pos]
        alive[pid] = True
        lengths[pid] = 1

    pellet = spawn_pellet(trails, p1_start, p2_start)

    return {
        "players": players,
        "positions": positions,
        "directions": directions,
        "trails": trails,
        "alive": alive,
        "lengths": lengths,
        "pellet": pellet,
        "turn_index": 0,
        "winner": None,
        "log": ["⚡ Lightcycle engines ignited! Trap your rival without crashing!"]
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    # Normalize integer dictionary keys
    raw_pos = state.get("positions", {})
    pos = {int(k): tuple(v) for k, v in raw_pos.items()} if isinstance(raw_pos, dict) else {}
    raw_alive = state.get("alive", {})
    alive = {int(k): v for k, v in raw_alive.items()} if isinstance(raw_alive, dict) else {}
    raw_len = state.get("lengths", {})
    lengths = {int(k): v for k, v in raw_len.items()} if isinstance(raw_len, dict) else {}
    raw_trails = state.get("trails", {})
    trails = {int(k): [tuple(c) for c in v] for k, v in raw_trails.items()} if isinstance(raw_trails, dict) else {}
    raw_dirs = state.get("directions", {})
    dirs = {int(k): tuple(v) for k, v in raw_dirs.items()} if isinstance(raw_dirs, dict) else {}

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "players": state["players"],
        "positions": pos,
        "directions": dirs,
        "trails": trails,
        "alive": alive,
        "lengths": lengths,
        "pellet": tuple(state["pellet"]) if state.get("pellet") else None,
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Steer: 'W' (Up), 'A' (Left), 'S' (Down), 'D' (Right) or 'L' (Turn Left), 'R' (Turn Right)"


def parse_action(state_or_view, player_id, raw_input):
    cmd = str(raw_input).strip().upper()
    if cmd in {"W", "A", "S", "D"}:
        return True, cmd
    # Relative steering
    if cmd in {"L", "R", "STRAIGHT", "F"}:
        return True, cmd
    return False, "Steering command must be W (Up), A (Left), S (Down), D (Right) or L/R."


def apply_action(state, player_id, cmd):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    opp = next(p for p in state["players"] if p["id"] != player_id)
    p_name = curr_p["name"]
    opp_name = opp["name"]
    opp_id = opp["id"]

    curr_dir = tuple(state["directions"][player_id])
    dx, dy = curr_dir

    # Calculate new direction
    if cmd in DIRS:
        new_dx, new_dy = DIRS[cmd]
        # Prevent instant 180° backward reversal
        if (new_dx, new_dy) == (-dx, -dy) and len(state["trails"][player_id]) > 1:
            new_dx, new_dy = dx, dy  # Maintain forward momentum
    elif cmd == "L":
        # 90° CCW turn: (dx, dy) -> (dy, -dx)
        new_dx, new_dy = dy, -dx
    elif cmd == "R":
        # 90° CW turn: (dx, dy) -> (-dy, dx)
        new_dx, new_dy = -dy, dx
    else:
        new_dx, new_dy = dx, dy

    state["directions"][player_id] = (new_dx, new_dy)
    curr_x, curr_y = state["positions"][player_id]
    next_x = curr_x + new_dx
    next_y = curr_y + new_dy
    next_pos = (next_x, next_y)

    log_entries = []

    # Check collisions
    crashed = False
    crash_reason = ""

    # 1. Wall collision
    if not (0 <= next_x < ARENA_WIDTH and 0 <= next_y < ARENA_HEIGHT):
        crashed = True
        crash_reason = "crashed into the boundary wall!"
    # 2. Own trail collision
    elif next_pos in state["trails"][player_id]:
        crashed = True
        crash_reason = "collided with their own light trail!"
    # 3. Opponent trail collision
    elif next_pos in state["trails"].get(opp_id, []):
        crashed = True
        crash_reason = f"slammed into {opp_name}'s light wall!"

    if crashed:
        state["alive"][player_id] = False
        state["winner"] = [opp_name]
        log_entries.append(f"💥 EXPLOSION! {p_name} {crash_reason}")
        log_entries.append(f"🏆 {opp_name} survives and WINS the Snake Duel!")
    else:
        state["positions"][player_id] = next_pos
        state["trails"][player_id].append(next_pos)

        # Check energy pellet
        if state.get("pellet") and next_pos == tuple(state["pellet"]):
            state["lengths"][player_id] = state["lengths"].get(player_id, 1) + 2
            log_entries.append(f"⭐ {p_name} absorbed an Energy Orb! Speed & trail expanded!")
            state["pellet"] = spawn_pellet(state["trails"], state["positions"][player_id], state["positions"][opp_id])
        else:
            log_entries.append(f"🏎️ {p_name} steered {cmd} to ({next_x}, {next_y}).")

    state["turn_index"] += 1
    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or not all(state.get("alive", {}).values())


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    if is_over(state):
        for p in state["players"]:
            if state["alive"].get(p["id"], False):
                return [p["name"]]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        # Auto-steer forward in current direction
        apply_action(state, player_id, "STRAIGHT")


def _render_arena(positions, directions, trails, alive, pellet, players):
    """Render the 2D Tron / Snake Duel arena."""
    p1 = players[0] if len(players) > 0 else {"id": 0}
    p2 = players[1] if len(players) > 1 else {"id": 1}

    t1_set = set(trails.get(p1["id"], []))
    t2_set = set(trails.get(p2["id"], []))

    p1_head = positions.get(p1["id"])
    p2_head = positions.get(p2["id"])

    p1_dir = directions.get(p1["id"], (1, 0))
    p2_dir = directions.get(p2["id"], (-1, 0))

    p1_icon = HEAD_ICONS.get(p1_dir, "▲")
    p2_icon = HEAD_ICONS.get(p2_dir, "▼")

    top_border = "  ┌" + "──" * ARENA_WIDTH + "┐"
    bot_border = "  └" + "──" * ARENA_WIDTH + "┘"
    rows = [top_border]

    for y in range(ARENA_HEIGHT):
        row_cells = []
        for x in range(ARENA_WIDTH):
            pt = (x, y)
            if pt == p1_head and alive.get(p1["id"], True):
                row_cells.append(paint(f"{p1_icon} ", "1;30;43"))  # P1 Head (Black on Yellow)
            elif pt == p2_head and alive.get(p2["id"], True):
                row_cells.append(paint(f"{p2_icon} ", "1;30;46"))  # P2 Head (Black on Cyan)
            elif pt == pellet:
                row_cells.append(paint("★ ", "1;33"))              # Energy Pellet
            elif pt in t1_set:
                row_cells.append(paint("■ ", "1;33"))              # P1 Trail
            elif pt in t2_set:
                row_cells.append(paint("■ ", "1;36"))              # P2 Trail
            else:
                row_cells.append("· ")                             # Empty grid dot

        rows.append("  │" + "".join(row_cells) + "│")

    rows.append(bot_border)
    return "\n".join(rows)


def render_dashboard(view):
    players = view.get("players", [])
    positions = view.get("positions", {})
    directions = view.get("directions", {})
    trails = view.get("trails", {})
    alive = view.get("alive", {})
    lengths = view.get("lengths", {})
    pellet = view.get("pellet")
    turn_id = view.get("turn_id")
    my_id = view.get("player_id")
    log = view.get("log", [])

    out = [
        paint("=" * 66, "1;36"),
        paint("               ⚡ S N A K E   D U E L ⚡", "1;36"),
        paint("=" * 66, "1;36"),
        ""
    ]

    p1 = players[0] if len(players) > 0 else {"id": 0, "name": "P1"}
    p2 = players[1] if len(players) > 1 else {"id": 1, "name": "P2"}

    st1 = paint("ALIVE", "1;32") if alive.get(p1["id"], True) else paint("CRASHED", "1;31")
    st2 = paint("ALIVE", "1;32") if alive.get(p2["id"], True) else paint("CRASHED", "1;31")

    out.append(f"  [P1] {p1['name']:<12}: Status: {st1} | Trail Length: {len(trails.get(p1['id'], []))}")
    out.append(f"  [P2] {p2['name']:<12}: Status: {st2} | Trail Length: {len(trails.get(p2['id'], []))}")
    out.append("")

    # Arena
    out.append(_render_arena(positions, directions, trails, alive, pellet, players))
    out.append("")

    out.append("  Controls: " + paint("W", "1;33") + "=Up  " +
               paint("A", "1;33") + "=Left  " +
               paint("S", "1;33") + "=Down  " +
               paint("D", "1;33") + "=Right  |  " +
               paint("★", "1;33") + " = Energy Orb")

    if log:
        out.append("")
        out.append("  Arena Activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  VICTORY! Champion: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Both Lightcycles crashed in a head-on tie!", "1;33"))
    return "\n".join(parts)
