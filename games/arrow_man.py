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
TOTAL_ROUNDS = 3

# Arrow Types
ARROW_TYPES = {
    "standard": {"name": "Standard Arrow 🎯", "bonus": 0, "wind_factor": 1.0, "icon": "»"},
    "fire":     {"name": "Fire Arrow 🔥", "bonus": 15, "wind_factor": 1.0, "icon": "🔥"},
    "pierce":   {"name": "Piercing Arrow 🗡️", "bonus": 10, "wind_factor": 0.2, "icon": "➔"},
    "bomb":     {"name": "Bomb Arrow 💥", "bonus": 20, "wind_factor": 1.1, "icon": "💥"},
}


def create_state(player_sessions):
    players = []
    # Dynamic randomized tower positions and elevations each round
    p1_x = random.randint(6, 14)
    p2_x = random.randint(ARENA_WIDTH - 15, ARENA_WIDTH - 7)
    t1_top = random.randint(8, 11)
    t2_top = random.randint(8, 11)

    hp = {}
    quivers = {}
    apples = {}
    positions = {}
    tower_tops = {}
    round_wins = {}

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
        tower_tops[pid] = t1_top if idx == 0 else t2_top
        round_wins[pid] = 0

    wind = random.randint(-4, 4)

    return {
        "players": players,
        "round": 1,
        "total_rounds": TOTAL_ROUNDS,
        "round_wins": round_wins,
        "hp": hp,
        "positions": positions,
        "tower_tops": tower_tops,
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
    raw_tops = state.get("tower_tops", {})
    tower_tops = {int(k): v for k, v in raw_tops.items()} if isinstance(raw_tops, dict) else {}
    raw_quiv = state.get("quivers", {})
    quivers = {int(k): v for k, v in raw_quiv.items()} if isinstance(raw_quiv, dict) else {}
    raw_apples = state.get("apples", {})
    apples = {int(k): v for k, v in raw_apples.items()} if isinstance(raw_apples, dict) else {}
    raw_wins = state.get("round_wins", {})
    round_wins = {int(k): v for k, v in raw_wins.items()} if isinstance(raw_wins, dict) else {}

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Archer",
        "opponent_name": opp["name"] if opp else "Rival",
        "players": state["players"],
        "round": state.get("round", 1),
        "total_rounds": state.get("total_rounds", TOTAL_ROUNDS),
        "round_wins": round_wins,
        "hp": hp,
        "positions": pos,
        "tower_tops": tower_tops,
        "quivers": quivers,
        "apples": apples,
        "wind": state.get("wind", 0),
        "last_shot": state.get("last_shot"),
        "trajectory": state.get("trajectory", []),
        "turn_id": current_player(state),
        "winner": state.get("winner"),
        "log": state.get("log", [])
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

    if not (0 <= angle <= 90):
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


def simulate_arrow_flight(p1_x, p2_x, shooter_idx, angle_deg, power, wind, arrow_type, opp_apple, t1_top=10, t2_top=10):
    """
    Simulate parabolic flight trajectory of the arrow.
    shooter_idx: 0 (Left shooting Right) or 1 (Right shooting Left)
    Returns: (trajectory_pts, hit_type, damage, impact_coord, apple_hit)
    hit_type: 'apple' | 'head' | 'body' | 'legs' | 'tower' | 'miss'
    """
    rad = math.radians(angle_deg)
    arrow_info = ARROW_TYPES.get(arrow_type, ARROW_TYPES["standard"])
    wind_factor = arrow_info["wind_factor"]

    # Direction and starting height
    if shooter_idx == 0:
        dir_mult = 1.0
        start_x = float(p1_x + 2)
        start_y = float(ARENA_HEIGHT - 1 - (t1_top - 2))  # bow height
        target_x = float(p2_x)
        opp_top = float(t2_top)
    else:
        dir_mult = -1.0
        start_x = float(p2_x - 2)
        start_y = float(ARENA_HEIGHT - 1 - (t2_top - 2))  # bow height
        target_x = float(p1_x)
        opp_top = float(t1_top)

    opp_base_y = float(ARENA_HEIGHT - 1 - opp_top)

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
        if target_left <= x <= target_right and 0 <= y <= opp_base_y + 6.0:
            # Hitboxes relative to opponent's tower platform (opp_base_y):
            # Apple: y >= opp_base_y + 3.8
            # Head: y >= opp_base_y + 2.5
            # Body: y >= opp_base_y + 1.2
            # Legs: y >= opp_base_y
            # Tower: y < opp_base_y
            if opp_apple and y >= opp_base_y + 3.8:
                apple_hit = True
                hit_type = "apple"
                damage = 30 + arrow_info["bonus"]
            elif y >= opp_base_y + 2.5:
                hit_type = "head"
                damage = 55 + arrow_info["bonus"]
            elif y >= opp_base_y + 1.2:
                hit_type = "body"
                damage = 35 + arrow_info["bonus"]
            elif y >= opp_base_y:
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
    t1_top = state.get("tower_tops", {}).get(state["players"][0]["id"], 10)
    t2_top = state.get("tower_tops", {}).get(state["players"][1]["id"], 10)

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
        p1_x, p2_x, shooter_idx, angle, power, wind, arrow_type, opp_apple, t1_top, t2_top
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

    # Check round/match victory
    p1_id = state["players"][0]["id"]
    p2_id = state["players"][1]["id"]
    p1_hp = state["hp"].get(p1_id, 0)
    p2_hp = state["hp"].get(p2_id, 0)

    round_finished = (p1_hp <= 0 or p2_hp <= 0)
    if round_finished:
        curr_round = state.get("round", 1)
        tot_rounds = state.get("total_rounds", TOTAL_ROUNDS)

        if p1_hp > 0 and p2_hp <= 0:
            round_winner_id = p1_id
            round_winner_name = state["players"][0]["name"]
        elif p2_hp > 0 and p1_hp <= 0:
            round_winner_id = p2_id
            round_winner_name = state["players"][1]["name"]
        else:
            round_winner_id = None
            round_winner_name = None

        if round_winner_id is not None:
            state["round_wins"][round_winner_id] = state["round_wins"].get(round_winner_id, 0) + 1
            log_entries.append(f"🏁 ROUND {curr_round} OVER! {round_winner_name} won Round {curr_round}!")
        else:
            log_entries.append(f"🏁 ROUND {curr_round} OVER! Round ended in a draw!")

        s1 = state["round_wins"].get(p1_id, 0)
        s2 = state["round_wins"].get(p2_id, 0)
        log_entries.append(f"   ➔ Standings: {state['players'][0]['name']} [{s1}] — [{s2}] {state['players'][1]['name']}")

        # Clinch match if a player achieves 2 round wins, or after 3 rounds
        if s1 >= 2 or s2 >= 2 or curr_round >= tot_rounds:
            if s1 > s2:
                state["winner"] = [state["players"][0]["name"]]
                log_entries.append(f"🏆 MATCH CHAMPION! {state['players'][0]['name']} reigns supreme ({s1} - {s2})!")
            elif s2 > s1:
                state["winner"] = [state["players"][1]["name"]]
                log_entries.append(f"🏆 MATCH CHAMPION! {state['players'][1]['name']} reigns supreme ({s2} - {s1})!")
            else:
                state["winner"] = []
                log_entries.append(f"🤝 DUEL TIED! Both archers drew the match ({s1} - {s2})!")
        else:
            state["round"] = curr_round + 1
            # Re-randomize positions and elevations for the next round
            state["positions"][p1_id] = random.randint(6, 14)
            state["positions"][p2_id] = random.randint(ARENA_WIDTH - 15, ARENA_WIDTH - 7)
            state["tower_tops"][p1_id] = random.randint(8, 11)
            state["tower_tops"][p2_id] = random.randint(8, 11)

            # Reset HP, Quivers, Apples
            for pid in state["hp"]:
                state["hp"][pid] = 100
            for pid in state["quivers"]:
                state["quivers"][pid] = {"fire": 1, "pierce": 1, "bomb": 1}
            for pid in state["apples"]:
                state["apples"][pid] = True

            state["wind"] = random.randint(-4, 4)
            state["trajectory"] = []

            # Alternate who starts the next round
            next_start_idx = (state["round"] - 1) % len(state["players"])
            state["turn_index"] = next_start_idx
            log_entries.append(f"🏹 Starting Round {state['round']} of {tot_rounds}! Towers relocated to new positions!")
    else:
        state["turn_index"] += 1

    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state.get("winner") is not None


def get_winner(state):
    if state.get("winner") is not None:
        return state["winner"]
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
    t1_top = state_or_view.get("tower_tops", {}).get(p1["id"], 10)
    t2_top = state_or_view.get("tower_tops", {}).get(p2["id"], 10)
    p1_hp = state_or_view["hp"].get(p1["id"], 100)
    p2_hp = state_or_view["hp"].get(p2["id"], 100)
    p1_apple = state_or_view.get("apples", {}).get(p1["id"], True)
    p2_apple = state_or_view.get("apples", {}).get(p2["id"], True)
    traj_set = set(state_or_view.get("trajectory", []))
    last_shot = state_or_view.get("last_shot")

    min_top = min(t1_top, t2_top)
    grid = [[" " for _ in range(ARENA_WIDTH)] for _ in range(ARENA_HEIGHT)]

    # Draw sky dots faintly
    for r in range(min_top):
        for c in range(ARENA_WIDTH):
            if (r + c) % 11 == 0:
                grid[r][c] = "·"

    # Draw Trajectory
    for (tc, tr) in traj_set:
        if 0 <= tc < ARENA_WIDTH and 0 <= tr < ARENA_HEIGHT:
            grid[tr][tc] = "•"

    # Draw Left Tower
    for r in range(t1_top, ARENA_HEIGHT):
        for c in range(p1_pos - 3, p1_pos + 4):
            if 0 <= c < ARENA_WIDTH:
                grid[r][c] = "═" if r == t1_top else "▒"

    # Draw Right Tower
    for r in range(t2_top, ARENA_HEIGHT):
        for c in range(p2_pos - 3, p2_pos + 4):
            if 0 <= c < ARENA_WIDTH:
                grid[r][c] = "═" if r == t2_top else "▒"

    # Draw Valley ground / water
    for c in range(p1_pos + 4, p2_pos - 3):
        if 0 <= c < ARENA_WIDTH:
            grid[ARENA_HEIGHT - 1][c] = "~"
            grid[ARENA_HEIGHT - 2][c] = "~"

    # Draw Archer 1 (Left, shooting East/Right from t1_top)
    if p1_hp > 0:
        if p1_apple:
            grid[t1_top - 4][p1_pos] = "🍎"
        grid[t1_top - 3][p1_pos] = "o"
        grid[t1_top - 2][p1_pos - 1] = "/"
        grid[t1_top - 2][p1_pos] = "|"
        grid[t1_top - 2][p1_pos + 1] = "\\"
        grid[t1_top - 2][p1_pos + 2] = "»"
        grid[t1_top - 1][p1_pos - 1] = "/"
        grid[t1_top - 1][p1_pos + 1] = "\\"
    else:
        grid[t1_top - 1][p1_pos] = "💀"

    # Draw Archer 2 (Right, shooting West/Left from t2_top)
    if p2_hp > 0:
        if p2_apple:
            grid[t2_top - 4][p2_pos] = "🍎"
        grid[t2_top - 3][p2_pos] = "o"
        grid[t2_top - 2][p2_pos - 2] = "«"
        grid[t2_top - 2][p2_pos - 1] = "/"
        grid[t2_top - 2][p2_pos] = "|"
        grid[t2_top - 2][p2_pos + 1] = "\\"
        grid[t2_top - 1][p2_pos - 1] = "/"
        grid[t2_top - 1][p2_pos + 1] = "\\"
    else:
        grid[t2_top - 1][p2_pos] = "💀"

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

    p1_pos = view.get("positions", {}).get(p1["id"], 8)
    p2_pos = view.get("positions", {}).get(p2["id"], ARENA_WIDTH - 9)
    t1_top = view.get("tower_tops", {}).get(p1["id"], 10)
    t2_top = view.get("tower_tops", {}).get(p2["id"], 10)

    hp1 = view.get("hp", {}).get(p1["id"], 100)
    hp2 = view.get("hp", {}).get(p2["id"], 100)
    quiv1 = view.get("quivers", {}).get(p1["id"], {})
    quiv2 = view.get("quivers", {}).get(p2["id"], {})
    turn_id = view.get("turn_id")
    wind = view.get("wind", 0)
    log = view.get("log", [])
    last_shot = view.get("last_shot")

    # Range and Elevation difference
    dist = abs(p2_pos - p1_pos)
    p1_elev = ARENA_HEIGHT - 1 - t1_top
    p2_elev = ARENA_HEIGHT - 1 - t2_top
    elev_diff = p2_elev - p1_elev
    elev_txt = f"{elev_diff:+d}m (Uphill)" if elev_diff > 0 else (f"{elev_diff:+d}m (Downhill)" if elev_diff < 0 else "0m (Level)")

    # Wind indicator
    if wind > 0:
        wind_txt = f"💨 WIND: {abs(wind)} mph East ➔➔➔"
    elif wind < 0:
        wind_txt = f"💨 WIND: {abs(wind)} mph West ◄◄◄"
    else:
        wind_txt = "💨 WIND: Calm (0 mph)"

    round_num = view.get("round", 1)
    tot_rounds = view.get("total_rounds", TOTAL_ROUNDS)
    rw = view.get("round_wins", {})
    s1 = rw.get(p1["id"], 0)
    s2 = rw.get(p2["id"], 0)
    round_header = f"⚔️ ROUND {round_num} OF {tot_rounds}  •  SCORE: {p1['name']} [{s1}] — [{s2}] {p2['name']}"

    out = [
        paint("=" * 70, "1;36"),
        paint("                 🏹 A R R O W   M A N   D U E L 🎯", "1;36"),
        paint(f"{round_header:^70}", "1;35"),
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
    out.append(f"   {paint(wind_txt, '1;33')}  |  {paint(f'Range: {dist}m', '1;37')}  |  {paint(f'Slope: {elev_txt}', '1;36')}")
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
    p1 = view.get("players", [])[0] if len(view.get("players", [])) > 0 else {"id": 0, "name": "P1"}
    p2 = view.get("players", [])[1] if len(view.get("players", [])) > 1 else {"id": 1, "name": "P2"}
    s1 = view.get("round_wins", {}).get(p1["id"], 0)
    s2 = view.get("round_wins", {}).get(p2["id"], 0)
    if winners:
        parts.append(paint(f"  🏆  VICTORY! Champion Archer: {', '.join(winners)} ({s1} - {s2})!  🏆", "1;32"))
    else:
        parts.append(paint(f"  Duel concluded in a draw ({s1} - {s2})!", "1;33"))
    return "\n".join(parts)
