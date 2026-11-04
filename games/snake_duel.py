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
turn_timeout = 6
direct_input = True

ARENA_WIDTH = 30
ARENA_HEIGHT = 14
POINTS_PER_FRUIT = 10
INITIAL_SNAKE_LENGTH = 2

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


def spawn_pellet(trails, *extra_positions):
    """Find empty arena cell for energy pellet, dynamically checking all snake trails and positions."""
    occupied = set()
    if isinstance(trails, dict):
        for t_list in trails.values():
            occupied.update(t_list)
    elif isinstance(trails, (list, tuple, set)):
        occupied.update(trails)

    for item in extra_positions:
        if isinstance(item, dict):
            occupied.update(item.values())
        elif isinstance(item, (list, tuple, set)):
            if len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], int):
                occupied.add(tuple(item))
            else:
                for sub in item:
                    if isinstance(sub, tuple):
                        occupied.add(sub)
                    elif isinstance(sub, dict):
                        occupied.update(sub.values())

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
    scores = {}

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
        lengths[pid] = INITIAL_SNAKE_LENGTH
        scores[pid] = 0

    pellet = spawn_pellet(trails, p1_start, p2_start)

    return {
        "players": players,
        "positions": positions,
        "directions": directions,
        "trails": trails,
        "alive": alive,
        "lengths": lengths,
        "scores": scores,
        "pellet": pellet,
        "turn_index": 0,
        "winner": None,
        "log": ["🐍 Endless Arena active! Eat 🍎 fruits to grow & score (+10 pts). Avoid crashing!"]
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
    raw_scores = state.get("scores", {})
    scores = {int(k): v for k, v in raw_scores.items()} if isinstance(raw_scores, dict) else {}
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
        "scores": scores,
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

    # Check energy fruit at destination
    eats_fruit = (state.get("pellet") and next_pos == tuple(state["pellet"]))

    # Check collisions
    crashed = False
    crash_reason = ""

    # 1. Wall collision
    if not (0 <= next_x < ARENA_WIDTH and 0 <= next_y < ARENA_HEIGHT):
        crashed = True
        crash_reason = "crashed into the boundary wall!"
    else:
        # Determine own occupied body tiles (tail vacates if slithering without fruit)
        curr_trail = state["trails"].get(player_id, [])
        curr_len = state["lengths"].get(player_id, INITIAL_SNAKE_LENGTH)
        if not eats_fruit and len(curr_trail) >= curr_len:
            own_body = curr_trail[1:]
        else:
            own_body = curr_trail

        # 2. Own body collision
        if next_pos in own_body:
            crashed = True
            crash_reason = "collided with their own snake body!"
        # 3. Opponent body collision
        elif next_pos in state["trails"].get(opp_id, []):
            crashed = True
            crash_reason = f"slammed into {opp_name}'s snake body!"
        # 4. Head-on collision
        elif next_pos == state["positions"].get(opp_id):
            crashed = True
            crash_reason = f"collided head-on with {opp_name}!"

    if crashed:
        state["alive"][player_id] = False
        state["winner"] = [opp_name]
        log_entries.append(f"💥 CRASH! {p_name} {crash_reason}")
        log_entries.append(f"🏆 {opp_name} survives and WINS the Snake Duel!")
    else:
        state["positions"][player_id] = next_pos
        state["trails"][player_id].append(next_pos)

        if eats_fruit:
            state["lengths"][player_id] = state["lengths"].get(player_id, INITIAL_SNAKE_LENGTH) + 1
            state["scores"][player_id] = state["scores"].get(player_id, 0) + POINTS_PER_FRUIT
            curr_score = state["scores"][player_id]
            log_entries.append(f"🍎 {p_name} ate a fruit! (+{POINTS_PER_FRUIT} pts) -> Total: {curr_score} pts | Length: {state['lengths'][player_id]}")
            state["pellet"] = spawn_pellet(state["trails"], state["positions"][player_id], state["positions"][opp_id])
        else:
            # Slither forward by trimming the tail to snake length
            while len(state["trails"][player_id]) > state["lengths"].get(player_id, INITIAL_SNAKE_LENGTH):
                state["trails"][player_id].pop(0)
            log_entries.append(f"🐍 {p_name} steered {cmd} to ({next_x}, {next_y}).")

    state["turn_index"] += 1
    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state.get("winner") is not None or not all(state.get("alive", {}).values())


def get_winner(state):
    if state.get("winner"):
        return state["winner"]
    if is_over(state):
        alive_players = [p for p in state["players"] if state.get("alive", {}).get(p["id"], False)]
        if len(alive_players) == 1:
            return [alive_players[0]["name"]]
        p1 = state["players"][0]
        p2 = state["players"][1]
        sc1 = state.get("scores", {}).get(p1["id"], 0)
        sc2 = state.get("scores", {}).get(p2["id"], 0)
        if sc1 > sc2:
            return [p1["name"]]
        elif sc2 > sc1:
            return [p2["name"]]
        else:
            return []
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
                row_cells.append("🍎")                              # Energy Fruit (2 columns wide)
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
    raw_pos = view.get("positions", {})
    positions = {int(k): tuple(v) for k, v in raw_pos.items()} if isinstance(raw_pos, dict) else {}
    raw_dirs = view.get("directions", {})
    directions = {int(k): tuple(v) for k, v in raw_dirs.items()} if isinstance(raw_dirs, dict) else {}
    raw_trails = view.get("trails", {})
    trails = {int(k): [tuple(c) for c in v] for k, v in raw_trails.items()} if isinstance(raw_trails, dict) else {}
    raw_alive = view.get("alive", {})
    alive = {int(k): v for k, v in raw_alive.items()} if isinstance(raw_alive, dict) else {}
    raw_len = view.get("lengths", {})
    lengths = {int(k): v for k, v in raw_len.items()} if isinstance(raw_len, dict) else {}
    raw_sc = view.get("scores", {})
    scores = {int(k): v for k, v in raw_sc.items()} if isinstance(raw_sc, dict) else {}
    pellet = tuple(view["pellet"]) if view.get("pellet") else None
    turn_id = view.get("turn_id")
    my_id = view.get("player_id")
    log = view.get("log", [])

    out = [
        paint("=" * 66, "1;36"),
        paint("               ⚡ S N A K E   D U E L ⚡", "1;36"),
        paint("   ♾️  ENDLESS SURVIVAL: Eat 🍎 to grow & score (+10 pts) | Outlast Rival   ", "1;37;44"),
        paint("=" * 66, "1;36"),
        ""
    ]

    p1 = players[0] if len(players) > 0 else {"id": 0, "name": "P1"}
    p2 = players[1] if len(players) > 1 else {"id": 1, "name": "P2"}

    st1 = paint("ALIVE", "1;32") if alive.get(p1["id"], True) else paint("CRASHED", "1;31")
    st2 = paint("ALIVE", "1;32") if alive.get(p2["id"], True) else paint("CRASHED", "1;31")

    sc1 = scores.get(p1["id"], 0)
    sc2 = scores.get(p2["id"], 0)
    len1 = len(trails.get(p1["id"], []))
    len2 = len(trails.get(p2["id"], []))

    p1_active = " ▶" if turn_id == p1["id"] else "  "
    p2_active = " ▶" if turn_id == p2["id"] else "  "

    out.append(f"{p1_active} [P1] {p1['name']:<12}: Status: {st1} | Score: {paint(f'{sc1} pts', '1;33')} | Length: {len1}")
    out.append(f"{p2_active} [P2] {p2['name']:<12}: Status: {st2} | Score: {paint(f'{sc2} pts', '1;36')} | Length: {len2}")
    out.append("")

    # Arena
    out.append(_render_arena(positions, directions, trails, alive, pellet, players))
    out.append("")

    out.append("  Controls: " + paint("W / ▲", "1;33") + "=Up  " +
               paint("A / ◄", "1;33") + "=Left  " +
               paint("S / ▼", "1;33") + "=Down  " +
               paint("D / ►", "1;33") + "=Right  |  [Direct Keypress — No Enter Needed!]")

    if log:
        out.append("")
        out.append("  Arena Activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    raw_sc = view.get("scores", {})
    scores = {int(k): v for k, v in raw_sc.items()} if isinstance(raw_sc, dict) else {}
    raw_len = view.get("lengths", {})
    lengths = {int(k): v for k, v in raw_len.items()} if isinstance(raw_len, dict) else {}
    players = view.get("players", [])

    if winners:
        winner_name = ", ".join(winners)
        parts.append(paint(f"  🏆  VICTORY! Champion: {winner_name}!  🏆", "1;32"))
    else:
        parts.append(paint("  Both snakes crashed in a head-on tie!", "1;33"))

    score_summary = "  Final Scores: " + "  vs  ".join(
        f"{p['name']}: {scores.get(p['id'], 0)} pts (Length: {lengths.get(p['id'], len(view.get('trails', {}).get(p['id'], [])))})" for p in players
    )
    parts.append(paint(score_summary, "1;36"))
    return "\n".join(parts)
