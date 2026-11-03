"""
Submarine Radar Hunt (Sonar) Game Module.
2-Player Competitive Stealth Naval Warfare with Dual Radar Displays, Sonar Pings, and Torpedoes.
"""
import random
from config import paint

game_id = "sonar"
game_name = "Sonar Submarine"
min_players = 2
max_players = 2

GRID_SIZE = 8
FILES = ["A", "B", "C", "D", "E", "F", "G", "H"]


def parse_coord(coord_str):
    s = str(coord_str).strip().upper()
    if len(s) != 2:
        return None
    f, r = s[0], s[1]
    if f not in FILES or not r.isdigit():
        return None
    c = FILES.index(f)
    row = int(r) - 1
    if 0 <= row < GRID_SIZE:
        return (row, c)
    return None


def to_coord(row, col):
    return f"{FILES[col]}{row + 1}"


def create_state(player_sessions):
    players = []
    positions = {}
    hp = {}
    torpedoes = {}
    pings = {}
    shots_history = {}  # pid -> {(r, c): 'hit' | 'near' | 'miss'}

    # Spawn submarines in different quadrants
    p1_pos = (random.randint(0, 3), random.randint(0, 3))
    p2_pos = (random.randint(4, 7), random.randint(4, 7))

    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        color = "1;36" if idx == 0 else "1;33"
        players.append({"id": pid, "name": name, "color": color, "token": f"SUB-{idx + 1}"})
        positions[pid] = p1_pos if idx == 0 else p2_pos
        hp[pid] = 3
        torpedoes[pid] = 4
        pings[pid] = 3
        shots_history[pid] = {}

    return {
        "players": players,
        "positions": positions,
        "hp": hp,
        "torpedoes": torpedoes,
        "pings": pings,
        "shots_history": shots_history,
        "turn_index": 0,
        "winner": None,
        "log": ["⚓ Submarines submerged! Rig for silent running and hunt the enemy vessel!"]
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    # Normalize integer dictionary keys
    raw_hp = state.get("hp", {})
    hp = {int(k): v for k, v in raw_hp.items()} if isinstance(raw_hp, dict) else {}
    raw_pos = state.get("positions", {})
    pos = {int(k): tuple(v) for k, v in raw_pos.items()} if isinstance(raw_pos, dict) else {}
    raw_torps = state.get("torpedoes", {})
    torps = {int(k): v for k, v in raw_torps.items()} if isinstance(raw_torps, dict) else {}
    raw_pings = state.get("pings", {})
    pings = {int(k): v for k, v in raw_pings.items()} if isinstance(raw_pings, dict) else {}

    # My tracking map of enemy coordinates
    my_shots = {}
    if player_id in state.get("shots_history", {}):
        for k_str, val in state["shots_history"][player_id].items():
            # handle tuple or str key
            coord = eval(k_str) if isinstance(k_str, str) and "(" in k_str else k_str
            my_shots[tuple(coord)] = val

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "players": state["players"],
        "my_pos": pos.get(player_id, (0, 0)),
        "my_hp": hp.get(player_id, 3),
        "opp_hp": hp.get(opp["id"], 3) if opp else 3,
        "my_torpedoes": torps.get(player_id, 4),
        "my_pings": pings.get(player_id, 3),
        "my_shots": my_shots,
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Commands: 'MOVE <N/S/E/W>', 'SONAR <A-H or 1-8>', 'TORPEDO <Coord>', 'SILENT'"


def parse_action(state_or_view, player_id, raw_input):
    parts = str(raw_input).strip().upper().split()
    if not parts:
        return False, "Enter command: 'MOVE <N/S/E/W>', 'SONAR <A-H or 1-8>', 'TORPEDO <Coord>' or 'SILENT'."

    cmd = parts[0]

    # 1. MOVE
    if cmd in {"MOVE", "M"}:
        if len(parts) < 2:
            return False, "Specify direction: 'MOVE N', 'MOVE S', 'MOVE E', or 'MOVE W'."
        d = parts[1][0]
        if d in {"N", "S", "E", "W"}:
            return True, {"action": "move", "dir": d}
        return False, f"Unknown direction '{d}'. Use N, S, E, or W."

    # Direct direction shorthand
    if cmd in {"N", "S", "E", "W"}:
        return True, {"action": "move", "dir": cmd}

    # 2. SONAR
    if cmd in {"SONAR", "PING", "P"}:
        if len(parts) < 2:
            return False, "Specify column (A–H) or row (1–8) for sonar ping (e.g. 'SONAR E' or 'SONAR 4')."
        target = parts[1]
        if target in FILES or (target.isdigit() and 1 <= int(target) <= 8):
            return True, {"action": "sonar", "target": target}
        return False, f"Invalid sonar target '{target}'. Must be Column (A–H) or Row (1–8)."

    # 3. TORPEDO
    if cmd in {"TORPEDO", "FIRE", "SHOOT", "T"}:
        if len(parts) < 2:
            return False, "Specify coordinate for torpedo launch (e.g. 'TORPEDO E4')."
        coord = parse_coord(parts[1])
        if not coord:
            return False, f"Invalid coordinate '{parts[1]}' (e.g. 'E4')."
        return True, {"action": "torpedo", "coord": coord, "text": parts[1]}

    # Direct coordinate shorthand e.g. "E4"
    coord = parse_coord(cmd)
    if coord:
        return True, {"action": "torpedo", "coord": coord, "text": cmd}

    # 4. SILENT RUNNING
    if cmd in {"SILENT", "WAIT", "PASS"}:
        return True, {"action": "silent"}

    return False, f"Unknown command '{cmd}'. Try 'MOVE N', 'SONAR E', 'TORPEDO E4', or 'SILENT'."


def apply_action(state, player_id, action_data):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    opp = next(p for p in state["players"] if p["id"] != player_id)
    p_name = curr_p["name"]
    opp_name = opp["name"]
    opp_id = opp["id"]

    act = action_data["action"]
    log_entries = []

    # 1. MOVE
    if act == "move":
        d = action_data["dir"]
        delta = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}[d]
        curr_r, curr_c = state["positions"][player_id]
        new_r = max(0, min(GRID_SIZE - 1, curr_r + delta[0]))
        new_c = max(0, min(GRID_SIZE - 1, curr_c + delta[1]))

        state["positions"][player_id] = (new_r, new_c)
        dir_names = {"N": "NORTH", "S": "SOUTH", "E": "EAST", "W": "WEST"}
        log_entries.append(f"🧭 {p_name} adjusted course: Propellers heard turning {dir_names[d]}!")

    # 2. SONAR
    elif act == "sonar":
        target = action_data["target"]
        opp_r, opp_c = state["positions"][opp_id]
        detected = False

        if target in FILES:
            col_idx = FILES.index(target)
            detected = (opp_c == col_idx)
        else:
            row_idx = int(target) - 1
            detected = (opp_r == row_idx)

        state["pings"][player_id] = max(0, state["pings"].get(player_id, 3) - 1)

        if detected:
            log_entries.append(f"📡 SONAR PING! {p_name} pinged Sector {target} ➔ ⚠️ ACOUSTIC CONTACT CONFIRMED!")
        else:
            log_entries.append(f"📡 SONAR PING! {p_name} pinged Sector {target} ➔ No acoustic reflection.")

    # 3. TORPEDO
    elif act == "torpedo":
        coord = action_data["coord"]
        tr, tc = coord
        coord_txt = action_data.get("text", to_coord(tr, tc))
        opp_r, opp_c = state["positions"][opp_id]

        state["torpedoes"][player_id] = max(0, state["torpedoes"].get(player_id, 4) - 1)

        # Distance calculation
        dist = max(abs(tr - opp_r), abs(tc - opp_c))

        if dist == 0:
            # Direct hit
            state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 3) - 2)
            state["shots_history"].setdefault(player_id, {})[str(coord)] = "hit"
            log_entries.append(f"💥 TORPEDO DIRECT HIT! {p_name} blasted {coord_txt}! {opp_name} takes 2 DAMAGE!")
        elif dist == 1:
            # Near miss shockwave
            state["hp"][opp_id] = max(0, state["hp"].get(opp_id, 3) - 1)
            state["shots_history"].setdefault(player_id, {})[str(coord)] = "near"
            log_entries.append(f"🌊 SHOCKWAVE HIT! {p_name} fired at {coord_txt}! Blast wave strikes {opp_name} (-1 HP)!")
        else:
            state["shots_history"].setdefault(player_id, {})[str(coord)] = "miss"
            log_entries.append(f"💦 Torpedo splash at {coord_txt}! Water detonation, no contact.")

    # 4. SILENT RUNNING
    elif act == "silent":
        log_entries.append(f"🤫 {p_name} rigged for silent running. Acoustic quiet maintained.")

    state["turn_index"] += 1

    # Check victory
    if state["hp"][opp_id] <= 0:
        state["winner"] = [p_name]
        log_entries.append(f"🏆 ENEMY VESSEL SUNK! {p_name} dominates the ocean and WINS!")

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


def _render_radar_maps(my_pos, my_shots):
    """Render side-by-side: Own Navigation Map vs Tactical Torpedo Map."""
    lines = []
    header = "      [OWN SUB NAVIGATION]              [TACTICAL TORPEDO RADAR]"
    col_hdr = "    A B C D E F G H                 A B C D E F G H"
    border  = "   ┌────────────────┐              ┌────────────────┐"
    bot_b   = "   └────────────────┘              └────────────────┘"

    lines.append(paint(header, "1;36"))
    lines.append(col_hdr)
    lines.append(border)

    for r in range(GRID_SIZE):
        row_num = r + 1
        # Left map (Own Sub)
        left_cells = []
        for c in range(GRID_SIZE):
            if (r, c) == my_pos:
                left_cells.append(paint("▲ ", "1;30;42"))  # Own sub icon
            else:
                left_cells.append("· ")

        # Right map (Tactical Shots)
        right_cells = []
        for c in range(GRID_SIZE):
            sh = my_shots.get((r, c))
            if sh == "hit":
                right_cells.append(paint("X ", "1;31"))  # Direct hit
            elif sh == "near":
                right_cells.append(paint("! ", "1;33"))  # Near miss
            elif sh == "miss":
                right_cells.append(paint("~ ", "1;34"))  # Water splash
            else:
                right_cells.append("· ")

        left_str = "".join(left_cells)
        right_str = "".join(right_cells)
        lines.append(f" {row_num} │{left_str}│            {row_num} │{right_str}│")

    lines.append(bot_b)
    return "\n".join(lines)


def render_dashboard(view):
    name = view.get("name", "Commander")
    opp_name = view.get("opponent_name", "Opponent")
    my_hp = view.get("my_hp", 3)
    opp_hp = view.get("opp_hp", 3)
    my_torps = view.get("my_torpedoes", 4)
    my_pings = view.get("my_pings", 3)
    my_pos = view.get("my_pos", (0, 0))
    my_shots = view.get("my_shots", {})
    turn_id = view.get("turn_id")
    my_id = view.get("player_id")
    log = view.get("log", [])

    out = [
        paint("=" * 66, "1;36"),
        paint("             ⚓ S O N A R   S U B M A R I N E ⚓", "1;36"),
        paint("=" * 66, "1;36"),
        ""
    ]

    # Health & Munitions
    hull_bar = paint("■ " * my_hp, "1;32") + paint("□ " * (3 - my_hp), "2")
    opp_hull = paint("■ " * opp_hp, "1;31") + paint("□ " * (3 - opp_hp), "2")

    out.append(f"  Your Hull Integrity : [{hull_bar}] ({my_hp}/3 HP)  | Sub Pos: {paint(to_coord(my_pos[0], my_pos[1]), '1;32')}")
    out.append(f"  Enemy Hull Status   : [{opp_hull}] ({opp_hp}/3 HP)  | Torpedoes: {my_torps} | Pings: {my_pings}")
    out.append("")

    # Dual Radar
    out.append(_render_radar_maps(my_pos, my_shots))
    out.append("")

    out.append("  Tactical Legend: " + paint("▲", "1;30;42") + " Your Sub  |  " +
               paint("X", "1;31") + " Direct Hit  |  " +
               paint("!", "1;33") + " Near Miss (1 HP)  |  " +
               paint("~", "1;34") + " Splash")

    if log:
        out.append("")
        out.append("  Acoustic Log:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  VICTORY! Sunk Enemy Vessel: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Both submarines lost in the deep!", "1;33"))
    return "\n".join(parts)
