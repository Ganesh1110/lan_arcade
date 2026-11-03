"""
Artillery Duel / Pocket Tanks Game Module.
2-Player Competitive Ballistic Tank Duel with Procedural Terrain, Wind Physics, and Destructible Slopes.
"""
import math
import random
from config import paint

game_id = "artillery"
game_name = "Artillery Duel"
min_players = 2
max_players = 2

WIDTH = 64
HEIGHT = 16
GRAVITY = 9.8


def generate_terrain():
    """Generate smooth procedural rolling hill heights across WIDTH columns."""
    heights = []
    base = 5
    freq1 = random.uniform(0.08, 0.14)
    freq2 = random.uniform(0.18, 0.25)
    phase1 = random.uniform(0, 3.14)
    phase2 = random.uniform(0, 3.14)

    for x in range(WIDTH):
        h = base + int(3.5 * math.sin(freq1 * x + phase1) + 2.0 * math.cos(freq2 * x + phase2))
        h = max(2, min(HEIGHT - 4, h))
        heights.append(h)
    return heights


def create_state(player_sessions):
    players = []
    terrain = generate_terrain()

    # Tank 1 on left hill (~col 8-12), Tank 2 on right hill (~col 50-54)
    t1_x = random.randint(6, 12)
    t2_x = random.randint(WIDTH - 14, WIDTH - 8)

    hp = {}
    positions = {}

    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        color = "1;33" if idx == 0 else "1;36"
        players.append({"id": pid, "name": name, "color": color, "token": f"T{idx + 1}"})
        hp[pid] = 100
        positions[pid] = t1_x if idx == 0 else t2_x

    wind = random.randint(-4, 4)

    return {
        "players": players,
        "terrain": terrain,
        "hp": hp,
        "positions": positions,
        "wind": wind,
        "last_shot": None,
        "trajectory": [],
        "turn_index": 0,
        "winner": None,
        "log": ["🎯 Artillery Duel initiated! Adjust angle & power to destroy the enemy tank!"]
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    # Normalize hp and positions with integer keys
    raw_hp = state.get("hp", {})
    hp = {int(k): v for k, v in raw_hp.items()} if isinstance(raw_hp, dict) else {}
    raw_pos = state.get("positions", {})
    pos = {int(k): v for k, v in raw_pos.items()} if isinstance(raw_pos, dict) else {}

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "players": state["players"],
        "terrain": state["terrain"],
        "hp": hp,
        "positions": pos,
        "wind": state["wind"],
        "last_shot": state.get("last_shot"),
        "trajectory": state.get("trajectory", []),
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter Angle (0–180°) and Power (1–100), e.g. '45 60' or '60 75'"


def parse_action(state_or_view, player_id, raw_input):
    parts = str(raw_input).strip().replace(",", " ").replace("°", "").split()
    if len(parts) < 2:
        return False, "Please enter two numbers: Angle and Power (e.g. '45 65')."
    try:
        angle = float(parts[0])
        power = float(parts[1])
    except ValueError:
        return False, "Angle and Power must be numeric values (e.g. '45 65')."

    if not (0 <= angle <= 180):
        return False, f"Angle must be between 0° and 180°, received {angle}°."
    if not (1 <= power <= 100):
        return False, f"Power must be between 1 and 100, received {power}."

    return True, {"angle": angle, "power": power}


def simulate_ballistic_flight(terrain, t_from_x, t_to_x, angle_deg, power, wind):
    """
    Simulate ballistic physics trajectory.
    Returns: (trajectory_points, impact_x, impact_y, direct_hit, damage)
    """
    rad = math.radians(angle_deg)
    # Velocity scaling
    v0 = power * 0.42
    vx = v0 * math.cos(rad)
    vy = v0 * math.sin(rad)
    wind_accel = wind * 0.12

    # Start coordinates (just above tank height)
    x0 = float(t_from_x)
    y0 = float(terrain[t_from_x] + 1)

    points = []
    t = 0.0
    dt = 0.12

    while t < 20.0:
        t += dt
        curr_x = x0 + vx * t + 0.5 * wind_accel * (t ** 2)
        curr_y = y0 + vy * t - 0.5 * GRAVITY * (t ** 2)

        ix = int(round(curr_x))
        iy = int(round(curr_y))

        if 0 <= ix < WIDTH:
            points.append((ix, iy))
            ground_h = terrain[ix]
            # Check impact with terrain or enemy tank
            if iy <= ground_h or iy <= 0:
                dist_to_enemy = abs(ix - t_to_x)
                if dist_to_enemy == 0:
                    return points, ix, ground_h, True, 50  # Direct bullseye!
                elif dist_to_enemy <= 2:
                    return points, ix, ground_h, False, 25  # Near miss blast
                else:
                    return points, ix, ground_h, False, 0   # Miss
        elif ix < 0 or ix >= WIDTH:
            # Flew off screen edges
            return points, ix, 0, False, 0

    return points, int(round(curr_x)), 0, False, 0


def apply_action(state, player_id, action_data):
    angle = action_data["angle"]
    power = action_data["power"]

    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    opp = next(p for p in state["players"] if p["id"] != player_id)
    p_name = curr_p["name"]
    opp_name = opp["name"]
    opp_id = opp["id"]

    t_from_x = state["positions"][player_id]
    t_to_x = state["positions"][opp_id]
    wind = state["wind"]

    # If player 2 (on the right), mirror angle if user typed intuitive left-facing angle
    eff_angle = angle
    if curr_p["token"] == "T2" and angle <= 90:
        eff_angle = 180 - angle

    traj, impact_x, impact_y, direct_hit, damage = simulate_ballistic_flight(
        state["terrain"], t_from_x, t_to_x, eff_angle, power, wind
    )
    state["trajectory"] = traj

    log_entries = []
    shot_desc = f"{angle:.0f}° @ {power:.0f}%"

    if direct_hit:
        state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 100) - damage)
        log_entries.append(f"💥 DIRECT HIT! {p_name} ({shot_desc}) landed a BULLSEYE on {opp_name}! -{damage} HP!")
    elif damage > 0:
        state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 100) - damage)
        log_entries.append(f"🎯 NEAR MISS! {p_name} ({shot_desc}) caught {opp_name} in blast radius! -{damage} HP!")
    else:
        log_entries.append(f"💨 {p_name} fired ({shot_desc}) — Shell struck earth at X={impact_x} (Miss).")

    # Crater terrain at impact site
    if 0 <= impact_x < WIDTH:
        state["terrain"][impact_x] = max(1, state["terrain"][impact_x] - 1)
        if impact_x > 0:
            state["terrain"][impact_x - 1] = max(1, state["terrain"][impact_x - 1] - 1)
        if impact_x < WIDTH - 1:
            state["terrain"][impact_x + 1] = max(1, state["terrain"][impact_x + 1] - 1)

    state["last_shot"] = {
        "player": p_name,
        "angle": angle,
        "power": power,
        "damage": damage,
        "direct": direct_hit
    }

    # Shift wind randomly for next turn
    state["wind"] = max(-5, min(5, state["wind"] + random.choice([-2, -1, 0, 1, 2])))
    state["turn_index"] += 1

    # Check game over
    if state["hp"][opp_id] <= 0:
        state["winner"] = [p_name]
        log_entries.append(f"🏆 ENEMY DESTROYED! {p_name} WINS the Artillery Duel!")

    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or any(hp <= 0 for hp in state.get("hp", {}).values())


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    if is_over(state):
        for p in state["players"]:
            if state["hp"].get(p["id"], 0) > 0:
                return [p["name"]]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def _render_battlefield(terrain, positions, players, trajectory):
    """Render ASCII terrain with sky, mountains, tanks, and shell trajectory arc."""
    traj_set = {(x, y) for x, y in trajectory if 0 <= x < WIDTH and 0 <= y < HEIGHT}

    p1_pos = positions.get(players[0]["id"], 10)
    p2_pos = positions.get(players[1]["id"], WIDTH - 10) if len(players) > 1 else WIDTH - 10

    grid = []
    for r in range(HEIGHT - 1, -1, -1):
        row_chars = []
        for c in range(WIDTH):
            h = terrain[c]
            # Tank 1 position
            if c == p1_pos and r == h + 1:
                row_chars.append(paint("T1", "1;30;43"))  # Tank 1 badge
            elif c == p2_pos and r == h + 1:
                row_chars.append(paint("T2", "1;30;46"))  # Tank 2 badge
            elif (c, r) in traj_set and r > h:
                row_chars.append(paint("•", "1;31"))       # Trajectory trace
            elif r <= h:
                # Ground / Mountain
                if r == h:
                    row_chars.append(paint("▲", "1;32"))   # Grass top
                else:
                    row_chars.append(paint("▒", "2"))      # Earth rock
            else:
                row_chars.append(" ")                     # Sky
        grid.append("  │" + "".join(row_chars) + "│")

    top_border = "  ┌" + "─" * WIDTH + "┐"
    bot_border = "  └" + "─" * WIDTH + "┘"
    return "\n".join([top_border] + grid + [bot_border])


def render_dashboard(view):
    players = view.get("players", [])
    raw_hp = view.get("hp", {})
    hp = {int(k): v for k, v in raw_hp.items()} if isinstance(raw_hp, dict) else {}
    positions = view.get("positions", {})
    terrain = view.get("terrain", [4] * WIDTH)
    wind = view.get("wind", 0)
    last_shot = view.get("last_shot")
    turn_id = view.get("turn_id")
    my_id = view.get("player_id")
    trajectory = view.get("trajectory", [])
    log = view.get("log", [])

    out = [
        paint("=" * 68, "1;36"),
        paint("             💣 A R T I L L E R Y   D U E L 💥", "1;36"),
        paint("=" * 68, "1;36"),
        ""
    ]

    # Health Bars & Wind Gauge
    p1 = players[0] if len(players) > 0 else {"id": 0, "name": "P1"}
    p2 = players[1] if len(players) > 1 else {"id": 1, "name": "P2"}
    hp1 = hp.get(p1["id"], 100)
    hp2 = hp.get(p2["id"], 100)

    # Health bar format: 10 segments
    bar1 = paint("█" * int(hp1 / 10), "1;32") + paint("░" * (10 - int(hp1 / 10)), "2")
    bar2 = paint("█" * int(hp2 / 10), "1;32") + paint("░" * (10 - int(hp2 / 10)), "2")

    wind_dir = "◄" * abs(wind) if wind < 0 else "►" * wind
    wind_label = f"Wind: {wind_dir} ({abs(wind)} mph)" if wind != 0 else "Wind: 0 mph (Calm)"

    out.append(f"  [T1] {p1['name']:<12}: [{bar1}] {hp1:3d} HP      {paint(wind_label, '1;33'):^18}")
    out.append(f"  [T2] {p2['name']:<12}: [{bar2}] {hp2:3d} HP")
    out.append("")

    # Battlefield
    out.append(_render_battlefield(terrain, positions, players, trajectory))
    out.append("")

    # Last Shot Feedback
    if last_shot:
        direct = "BULLSEYE DIRECT HIT!" if last_shot.get("direct") else (f"HIT! (-{last_shot['damage']} HP)" if last_shot["damage"] > 0 else "MISS (Impact in dirt)")
        out.append(f"  Last Shot: {last_shot['player']} fired {last_shot['angle']:.0f}° @ {last_shot['power']:.0f}% ➔ {paint(direct, '1;33')}")
        out.append("")

    if log:
        out.append("  Battle Activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  VICTORY! Winner: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Artillery duel ended in a draw!", "1;33"))
    return "\n".join(parts)
