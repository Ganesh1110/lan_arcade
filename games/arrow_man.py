"""
Arrow Man Duel / Bowman Archery Game Module.
2-Player Competitive Turn-based Archery Duel with Stickman Archers, Parabolic Physics,
Dynamic Crosswinds, Hit Zones (Head, Apple, Body, Legs), and Special Arrows.
"""
import math
import random
from config import paint

game_id = "arrow_man"
game_name = "Arrow Man Duel 🏹"
min_players = 2
max_players = 2
turn_timeout = 30
direct_input = False

ARENA_WIDTH = 66
ARENA_HEIGHT = 16
GRAVITY = 9.8

# Arrow Types
ARROW_TYPES = {
    "standard": {"name": "Standard Arrow 🎯", "bonus": 0, "wind_factor": 1.0, "icon": "»"},
    "fire":     {"name": "Fire Arrow 🔥", "bonus": 15, "wind_factor": 1.0, "icon": "🔥"},
    "pierce":   {"name": "Piercing Arrow 🗡️", "bonus": 10, "wind_factor": 0.2, "icon": "➔"},
    "bomb":     {"name": "Bomb Arrow 💥", "bonus": 20, "wind_factor": 1.1, "icon": "💥"},
}


def create_state(player_sessions):
    players = []
    # Fixed towers for clean stickman presentation
    p1_x = 8
    p2_x = ARENA_WIDTH - 9

    hp = {}
    quivers = {}
    apples = {}
    positions = {}

    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        color = "1;33" if idx == 0 else "1;36"
        token = f"P{idx + 1}"
        players.append({"id": pid, "name": name, "color": color, "token": token})

        hp[pid] = 100
        quivers[pid] = {"fire": 1, "pierce": 1, "bomb": 1}
        apples[pid] = True  # Apple sitting on head
        positions[pid] = p1_x if idx == 0 else p2_x

    wind = random.randint(-4, 4)

    return {
        "players": players,
        "hp": hp,
        "positions": positions,
        "quivers": quivers,
        "apples": apples,
        "wind": wind,
        "last_shot": None,
        "trajectory": [],
        "turn_index": 0,
        "winner": None,
        "log": ["🏹 Archery duel commenced! Ready your bow, judge the wind, and draw!"]
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    raw_hp = state.get("hp", {})
    hp = {int(k): v for k, v in raw_hp.items()} if isinstance(raw_hp, dict) else {}
    raw_pos = state.get("positions", {})
    pos = {int(k): v for k, v in raw_pos.items()} if isinstance(raw_pos, dict) else {}
    raw_quiv = state.get("quivers", {})
    quivers = {int(k): v for k, v in raw_quiv.items()} if isinstance(raw_quiv, dict) else {}
    raw_apples = state.get("apples", {})
    apples = {int(k): v for k, v in raw_apples.items()} if isinstance(raw_apples, dict) else {}

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Archer",
        "opponent_name": opp["name"] if opp else "Rival",
        "players": state["players"],
        "hp": hp,
        "positions": pos,
        "quivers": quivers,
        "apples": apples,
        "wind": state.get("wind", 0),
        "last_shot": state.get("last_shot"),
        "trajectory": state.get("trajectory", []),
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Aim: '<angle> <power>' (e.g. '45 70') | Optional arrow: 'fire', 'pierce', 'bomb' (e.g. '45 75 fire')"


def parse_action(state_or_view, player_id, raw_input):
    parts = str(raw_input).strip().lower().replace(",", " ").replace("°", "").split()
    if not parts:
        return False, "Enter Angle (0–90°) and Power (1–100), e.g. '45 70' or '50 80 fire'."

    arrow_type = "standard"
    numeric_parts = []

    for p in parts:
        if p in ARROW_TYPES:
            arrow_type = p
        elif p in {"f", "flame"}:
            arrow_type = "fire"
        elif p in {"p", "sniper"}:
            arrow_type = "pierce"
        elif p in {"b", "boom"}:
            arrow_type = "bomb"
        else:
            numeric_parts.append(p)

    if len(numeric_parts) < 2:
        return False, "Please enter both Angle (0–90°) and Power (1–100), e.g. '45 70'."

    try:
        angle = float(numeric_parts[0])
        power = float(numeric_parts[1])
    except ValueError:
        return False, "Angle and Power must be numbers (e.g. '45 70')."

    if not (0 <= angle <= 90 or 90 <= angle <= 180):
        return False, f"Angle must be between 0° and 90° (elevation), received {angle}°."
    if not (1 <= power <= 100):
        return False, f"Power must be between 1 and 100, received {power}."

    # Validate quiver charge
    quivers = state_or_view.get("quivers", {})
    if isinstance(quivers, dict) and player_id in quivers:
        p_quiv = quivers[player_id]
        if arrow_type != "standard" and p_quiv.get(arrow_type, 0) <= 0:
            return False, f"You have no {ARROW_TYPES[arrow_type]['name']} remaining! Use standard arrow."

    return True, {"angle": angle, "power": power, "arrow": arrow_type}


def simulate_arrow_flight(p1_x, p2_x, shooter_idx, angle_deg, power, wind, arrow_type, opp_apple):
    """
    Simulate parabolic flight trajectory of the arrow.
    shooter_idx: 0 (Left shooting Right) or 1 (Right shooting Left)
    Returns: (trajectory_pts, hit_type, damage, impact_coord, apple_hit)
    hit_type: 'apple' | 'head' | 'body' | 'legs' | 'tower' | 'miss'
    """
    rad = math.radians(angle_deg)
    arrow_info = ARROW_TYPES.get(arrow_type, ARROW_TYPES["standard"])
    wind_factor = arrow_info["wind_factor"]

    # Direction: Left shooter flies rightward (+x), Right shooter flies leftward (-x)
    if shooter_idx == 0:
        dir_mult = 1.0
        start_x = float(p1_x + 2)
        target_x = float(p2_x)
    else:
        dir_mult = -1.0
        start_x = float(p2_x - 2)
        target_x = float(p1_x)

    # Archer vertical hitboxes on tower:
    # Tower top is at row 10. Archer stands rows 6..9
    # Row 6: Apple (if present)
    # Row 7: Head
    # Row 8: Torso / Arms
    # Row 9: Legs
    # Row 10..15: Tower base
    start_y = 7.0  # bow height

    v0 = power * 0.44
    vx = v0 * math.cos(rad) * dir_mult
    vy = v0 * math.sin(rad)  # up in physical coordinates

    wind_accel = wind * 0.10 * wind_factor

    dt = 0.08
    t = 0.0
    x, y = start_x, start_y
    trajectory = []

    hit_type = "miss"
    damage = 0
    apple_hit = False

    target_left = target_x - 1.5
    target_right = target_x + 1.5

    while t < 6.0:
        # Physical coordinates: y is height above ground (0 = bottom, 15 = top)
        # Terminal rows: row 0 is top sky, row 15 is ground
        grid_col = int(round(x))
        grid_row = int(round(ARENA_HEIGHT - 1 - y))

        if 0 <= grid_col < ARENA_WIDTH and 0 <= grid_row < ARENA_HEIGHT:
            if not trajectory or trajectory[-1] != (grid_col, grid_row):
                trajectory.append((grid_col, grid_row))

        # Check collision with opponent archer column
        if target_left <= x <= target_right and 0 <= y <= 12:
            # Check vertical zones (y in height coords):
            # Apple: y ~ 9.5 to 10.5 (Row 5-6)
            # Head: y ~ 8.0 to 9.4 (Row 7)
            # Body: y ~ 6.5 to 7.9 (Row 8)
            # Legs: y ~ 5.0 to 6.4 (Row 9)
            # Tower: y < 5.0 (Row 10+)
            if opp_apple and y >= 9.5:
                apple_hit = True
                hit_type = "apple"
                damage = 30 + arrow_info["bonus"]
            elif y >= 8.0:
                hit_type = "head"
                damage = 55 + arrow_info["bonus"]
            elif y >= 6.5:
                hit_type = "body"
                damage = 35 + arrow_info["bonus"]
            elif y >= 5.0:
                hit_type = "legs"
                damage = 20 + arrow_info["bonus"]
            else:
                hit_type = "tower"
                damage = 10 if arrow_type == "bomb" else 0
            break

        # Check ground collision
        if y <= 0:
            hit_type = "miss"
            break

        # Check out of horizontal bounds
        if x < -5 or x > ARENA_WIDTH + 5:
            hit_type = "miss"
            break

        t += dt
        vx += wind_accel * dt
        vy -= GRAVITY * 0.40 * dt
        x += vx * dt
        y += vy * dt

    return trajectory, hit_type, damage, (int(round(x)), int(round(ARENA_HEIGHT - 1 - y))), apple_hit


def apply_action(state, player_id, action_data):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    opp = next(p for p in state["players"] if p["id"] != player_id)
    p_name = curr_p["name"]
    opp_name = opp["name"]
    opp_id = opp["id"]

    shooter_idx = 0 if state["players"][0]["id"] == player_id else 1
    p1_x = state["positions"][state["players"][0]["id"]]
    p2_x = state["positions"][state["players"][1]["id"]]

    angle = action_data["angle"]
    power = action_data["power"]
    arrow_type = action_data.get("arrow", "standard")

    # Consume special arrow
    if arrow_type != "standard":
        state["quivers"][player_id][arrow_type] = max(0, state["quivers"][player_id].get(arrow_type, 1) - 1)

    opp_apple = state["apples"].get(opp_id, True)
    wind = state.get("wind", 0)

    # Simulate arrow flight
    traj, hit_type, dmg, impact, apple_struck = simulate_arrow_flight(
        p1_x, p2_x, shooter_idx, angle, power, wind, arrow_type, opp_apple
    )

    state["trajectory"] = traj
    arrow_title = ARROW_TYPES[arrow_type]["name"]
    log_entries = []

    arrow_spec = f"{angle:.0f}° @ {power:.0f}% with {arrow_title}"

    if hit_type == "apple" and apple_struck:
        state["apples"][opp_id] = False
        state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 100) - dmg)
        # Reward shooter with HP recovery & fresh bomb arrow
        state["hp"][player_id] = min(100, state["hp"].get(player_id, 100) + 20)
        state["quivers"][player_id]["bomb"] = state["quivers"][player_id].get("bomb", 0) + 1
        log_entries.append(f"🍎 INCREDIBLE SHOT! {p_name} shot the apple off {opp_name}'s head!")
        log_entries.append(f"   ➔ +20 HP heal & bonus Bomb Arrow awarded! ({dmg} dmg to rival)")
    elif hit_type == "head":
        state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 100) - dmg)
        log_entries.append(f"🎯 CRITICAL HEADSHOT! {p_name} shot {arrow_spec}!")
        log_entries.append(f"   ➔ Massive strike! {opp_name} suffers -{dmg} HP damage!")
    elif hit_type == "body":
        state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 100) - dmg)
        log_entries.append(f"🏹 DIRECT BODY HIT! {p_name} struck {opp_name}'s torso (-{dmg} HP)!")
    elif hit_type == "legs":
        state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 100) - dmg)
        log_entries.append(f"🦵 GRAZING LEG SHOT! {p_name} hit {opp_name}'s leg (-{dmg} HP)!")
    elif hit_type == "tower":
        if dmg > 0:
            state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 100) - dmg)
            log_entries.append(f"💥 BOMB IMPACT! {p_name} blasted the tower platform! Splash deals -{dmg} HP!")
        else:
            log_entries.append(f"🛡️ Tower strike! {p_name}'s arrow thudded into the tower wood. No damage.")
    else:
        log_entries.append(f"💨 Missed! {p_name}'s arrow sailed into the valley water ({arrow_spec}).")

    state["last_shot"] = {
        "player": p_name,
        "angle": angle,
        "power": power,
        "arrow": arrow_type,
        "hit": hit_type,
        "damage": dmg
    }

    # Shift wind for next turn
    state["wind"] = max(-5, min(5, state.get("wind", 0) + random.randint(-2, 2)))

    # Check victory
    if state["hp"][opp_id] <= 0:
        state["winner"] = [p_name]
        log_entries.append(f"🏆 VICTORY! {p_name} felled {opp_name} and reigns supreme as Master Archer!")

    state["turn_index"] += 1
    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    if state.get("winner") is not None:
        return True
    return any(hp <= 0 for hp in state.get("hp", {}).values())


def get_winner(state):
    if state.get("winner"):
        return state["winner"]
    if is_over(state):
        for p in state["players"]:
            if state.get("hp", {}).get(p["id"], 0) > 0:
                return [p["name"]]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        # Default safety shot
        apply_action(state, player_id, {"angle": 45, "power": 50, "arrow": "standard"})


def _render_arena(state_or_view):
    p1 = state_or_view["players"][0]
    p2 = state_or_view["players"][1]
    p1_pos = state_or_view["positions"].get(p1["id"], 8)
    p2_pos = state_or_view["positions"].get(p2["id"], ARENA_WIDTH - 9)
    p1_hp = state_or_view["hp"].get(p1["id"], 100)
    p2_hp = state_or_view["hp"].get(p2["id"], 100)
    p1_apple = state_or_view.get("apples", {}).get(p1["id"], True)
    p2_apple = state_or_view.get("apples", {}).get(p2["id"], True)
    traj_set = set(state_or_view.get("trajectory", []))
    last_shot = state_or_view.get("last_shot")

    # Tower heights & geometry
    tower_top_row = 10
    grid = [[" " for _ in range(ARENA_WIDTH)] for _ in range(ARENA_HEIGHT)]

    # Draw sky dots faintly
    for r in range(tower_top_row):
        for c in range(ARENA_WIDTH):
            if (r + c) % 11 == 0:
                grid[r][c] = "·"

    # Draw Trajectory
    for (tc, tr) in traj_set:
        if 0 <= tc < ARENA_WIDTH and 0 <= tr < ARENA_HEIGHT:
            grid[tr][tc] = "•"

    # Draw Towers
    for r in range(tower_top_row, ARENA_HEIGHT):
        # Left tower
        for c in range(p1_pos - 3, p1_pos + 4):
            if 0 <= c < ARENA_WIDTH:
                grid[r][c] = "═" if r == tower_top_row else "▒"
        # Right tower
        for c in range(p2_pos - 3, p2_pos + 4):
            if 0 <= c < ARENA_WIDTH:
                grid[r][c] = "═" if r == tower_top_row else "▒"

    # Draw Valley ground / water
    for c in range(p1_pos + 4, p2_pos - 3):
        if 0 <= c < ARENA_WIDTH:
            grid[ARENA_HEIGHT - 1][c] = "~"
            grid[ARENA_HEIGHT - 2][c] = "~"

    # Draw Archer 1 (Left, shooting East/Right)
    if p1_hp > 0:
        if p1_apple:
            grid[5][p1_pos] = "🍎"
        grid[6][p1_pos] = "o"
        grid[7][p1_pos - 1] = "/"
        grid[7][p1_pos] = "|"
        grid[7][p1_pos + 1] = "\\"
        grid[7][p1_pos + 2] = "»"
        grid[8][p1_pos - 1] = "/"
        grid[8][p1_pos + 1] = "\\"
    else:
        grid[9][p1_pos] = "💀"

    # Draw Archer 2 (Right, shooting West/Left)
    if p2_hp > 0:
        if p2_apple:
            grid[5][p2_pos] = "🍎"
        grid[6][p2_pos] = "o"
        grid[7][p2_pos - 2] = "«"
        grid[7][p2_pos - 1] = "/"
        grid[7][p2_pos] = "|"
        grid[7][p2_pos + 1] = "\\"
        grid[8][p2_pos - 1] = "/"
        grid[8][p2_pos + 1] = "\\"
    else:
        grid[9][p2_pos] = "💀"

    # Compile painted rows
    rendered_rows = []
    top_b = "  ┌" + "─" * ARENA_WIDTH + "┐"
    bot_b = "  └" + "─" * ARENA_WIDTH + "┘"
    rendered_rows.append(top_b)

    for r in range(ARENA_HEIGHT):
        row_chars = []
        c = 0
        while c < ARENA_WIDTH:
            ch = grid[r][c]
            # Apple emoji occupies 2 columns
            if ch == "🍎":
                row_chars.append("🍎")
                c += 1
            elif (c, r) in traj_set:
                row_chars.append(paint("•", "1;31"))
            elif ch in {"o", "/", "\\", "|", "»", "«"}:
                # Archer color
                color = "1;33" if c < ARENA_WIDTH // 2 else "1;36"
                row_chars.append(paint(ch, color))
            elif ch == "💀":
                row_chars.append(paint("💀", "1;31"))
            elif ch in {"═", "▒"}:
                row_chars.append(paint(ch, "2;37"))
            elif ch == "~":
                row_chars.append(paint(ch, "1;34"))
            elif ch == "·":
                row_chars.append(paint(ch, "2"))
            else:
                row_chars.append(ch)
            c += 1
        rendered_rows.append("  │" + "".join(row_chars) + "│")

    rendered_rows.append(bot_b)
    return "\n".join(rendered_rows)


def render_dashboard(view):
    players = view.get("players", [])
    p1 = players[0] if len(players) > 0 else {"id": 0, "name": "P1"}
    p2 = players[1] if len(players) > 1 else {"id": 1, "name": "P2"}

    hp1 = view.get("hp", {}).get(p1["id"], 100)
    hp2 = view.get("hp", {}).get(p2["id"], 100)
    quiv1 = view.get("quivers", {}).get(p1["id"], {})
    quiv2 = view.get("quivers", {}).get(p2["id"], {})
    turn_id = view.get("turn_id")
    wind = view.get("wind", 0)
    log = view.get("log", [])
    last_shot = view.get("last_shot")

    # Wind indicator
    if wind > 0:
        wind_txt = f"💨 WIND: {abs(wind)} mph East ➔➔➔"
    elif wind < 0:
        wind_txt = f"💨 WIND: {abs(wind)} mph West ◄◄◄"
    else:
        wind_txt = "💨 WIND: Calm (0 mph)"

    out = [
        paint("=" * 70, "1;36"),
        paint("                 🏹 A R R O W   M A N   D U E L 🎯", "1;36"),
        paint("=" * 70, "1;36"),
        ""
    ]

    # Health Bars (10 blocks = 100 HP)
    bar1 = paint("█" * (hp1 // 10), "1;32") + paint("░" * (10 - (hp1 // 10)), "2")
    bar2 = paint("█" * (hp2 // 10), "1;32") + paint("░" * (10 - (hp2 // 10)), "2")

    p1_active = " ▶" if turn_id == p1["id"] else "  "
    p2_active = " ▶" if turn_id == p2["id"] else "  "

    out.append(f"{p1_active} [P1] {p1['name']:<12}: [{bar1}] {hp1:3d} HP | Quiver: 🔥x{quiv1.get('fire', 0)} 🗡️x{quiv1.get('pierce', 0)} 💥x{quiv1.get('bomb', 0)}")
    out.append(f"{p2_active} [P2] {p2['name']:<12}: [{bar2}] {hp2:3d} HP | Quiver: 🔥x{quiv2.get('fire', 0)} 🗡️x{quiv2.get('pierce', 0)} 💥x{quiv2.get('bomb', 0)}")
    out.append(f"      {paint(wind_txt, '1;33'):^58}")
    out.append("")

    # Visual Battlefield
    out.append(_render_arena(view))
    out.append("")

    # Tactical controls guide
    out.append("  Aiming : " + paint("<Angle 0–90°> <Power 1–100>", "1;33") + " (e.g. '45 70')")
    out.append("  Arrows : " + paint("standard", "1;32") + " (∞), " +
               paint("fire", "1;31") + " (+15 burn), " +
               paint("pierce", "1;36") + " (ignores wind), " +
               paint("bomb", "1;35") + " (+20 blast)")
    out.append("  Hitbox : 🍎 Apple (+heal/bomb)  |  🎯 Head (55 dmg)  |  🏹 Body (35 dmg)  |  🦵 Leg (20 dmg)")

    if log:
        out.append("")
        out.append("  Battle Log:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  VICTORY! Champion Archer: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Both archers fell in a draw!", "1;33"))
    return "\n".join(parts)
