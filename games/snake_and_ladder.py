"""
Snake & Ladders Game Module.
2–4 Player Classic Board Game.
"""
import random
from config import paint

game_id = "snake_and_ladder"
game_name = "Snake & Ladders"
min_players = 2
max_players = 4

# Classic Ladders mapping: start -> end
LADDERS = {
    2: 38,
    4: 14,
    9: 31,
    21: 42,
    28: 84,
    36: 44,
    51: 67,
    71: 91,
    80: 100
}

# Classic Snakes mapping: head -> tail
SNAKES = {
    16: 6,
    47: 26,
    49: 11,
    56: 53,
    62: 19,
    64: 60,
    87: 24,
    93: 73,
    95: 75,
    98: 78
}

PLAYER_COLORS = ["1;33", "1;36", "1;35", "1;32"]

# Distinct badge styling for each player token on the board:
# P1: Black text on Bright Yellow background
# P2: Black text on Bright Cyan background
# P3: Black text on Bright Magenta background
# P4: Black text on Bright Green background
PLAYER_BADGE_STYLES = {
    "P1": "1;30;43",
    "P2": "1;30;46",
    "P3": "1;30;45",
    "P4": "1;30;42",
}


def create_state(player_sessions):
    players = []
    positions = {}

    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        color = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
        players.append({"id": pid, "name": name, "color": color, "token": f"P{idx + 1}"})
        positions[pid] = 1  # All players start at square 1

    return {
        "players": players,
        "positions": positions,
        "turn_index": 0,
        "last_roll": None,
        "last_movement": None,
        "winner": None,
        "log": ["🎲 Game started! All players start at Square 1."]
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "players": state["players"],
        "positions": state["positions"],
        "turn_id": current_player(state),
        "last_roll": state["last_roll"],
        "last_movement": state.get("last_movement"),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Press [ENTER] or type 'r' to roll the die"


def parse_action(state_or_view, player_id, raw_input):
    # Any input or enter key rolls the die
    return True, "roll"


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    p_name = curr_p["name"]
    curr_pos = state["positions"][player_id]

    roll = random.randint(1, 6)
    state["last_roll"] = roll
    log_entries = []

    movement_info = {
        "player_id": player_id,
        "player_name": p_name,
        "token": curr_p["token"],
        "roll": roll,
        "from_sq": curr_pos,
        "rolled_to": curr_pos,
        "final_sq": curr_pos,
        "type": "normal",
        "ladder_to": None,
        "snake_to": None
    }

    if curr_pos + roll > 100:
        movement_info["type"] = "overshoot"
        log_entries.append(
            f"🎲 {p_name} rolled a {roll}! Overshoot! Needs exact roll to reach 100. Stays at Square {curr_pos}."
        )
        state["turn_index"] += 1
    else:
        rolled_sq = curr_pos + roll
        new_pos = rolled_sq
        movement_info["rolled_to"] = rolled_sq
        log_entries.append(f"🎲 {p_name} rolled a {roll}! Moved from Square {curr_pos} to {rolled_sq}.")

        if rolled_sq in LADDERS:
            dest = LADDERS[rolled_sq]
            movement_info["type"] = "ladder"
            movement_info["ladder_to"] = dest
            log_entries.append(f"🪜 LADDER! {p_name} climbed from Square {rolled_sq} up to {dest}!")
            new_pos = dest
        elif rolled_sq in SNAKES:
            dest = SNAKES[rolled_sq]
            movement_info["type"] = "snake"
            movement_info["snake_to"] = dest
            log_entries.append(f"🐍 SNAKE! {p_name} slid down from Square {rolled_sq} to {dest}!")
            new_pos = dest

        movement_info["final_sq"] = new_pos
        state["positions"][player_id] = new_pos

        if new_pos == 100:
            state["winner"] = [p_name]
            log_entries.append(f"🎉 {p_name} reached Square 100 and WINS the game!")
        elif roll == 6:
            log_entries.append(f"🔥 {p_name} rolled a 6 and gets an EXTRA TURN!")
        else:
            state["turn_index"] += 1

    state["last_movement"] = movement_info
    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def _render_board_grid(positions, players, last_movement=None):
    # Map square number to tokens present
    sq_tokens = {}
    for p in players:
        pid = p["id"]
        token = p.get("token", f"P{pid + 1}")
        # Look up int pid and str pid cleanly
        pos = positions.get(pid)
        if pos is None:
            pos = positions.get(str(pid), 1)
        sq_tokens.setdefault(pos, []).append(token)

    top_b = "  ┌" + "──────┬" * 9 + "──────┐"
    mid_b = "  ├" + "──────┼" * 9 + "──────┤"
    bot_b = "  └" + "──────┴" * 9 + "──────┘"
    rows = [top_b]

    for r in range(10, 0, -1):
        row_cells = []
        if r % 2 == 0:
            squares = list(range(r * 10, (r - 1) * 10, -1))
        else:
            squares = list(range((r - 1) * 10 + 1, r * 10 + 1))

        for sq in squares:
            tokens = sq_tokens.get(sq, [])
            if tokens:
                if len(tokens) == 1:
                    tok = tokens[0]
                    style = PLAYER_BADGE_STYLES.get(tok, "1;30;43")
                    formatted = paint(f" [{tok}] ", style)
                elif len(tokens) == 2:
                    t1, t2 = tokens[0], tokens[1]
                    s1 = PLAYER_BADGE_STYLES.get(t1, "1;30;43")
                    s2 = PLAYER_BADGE_STYLES.get(t2, "1;30;46")
                    formatted = paint(t1, s1) + "," + paint(t2, s2) + " "
                elif len(tokens) == 3:
                    formatted = "".join(paint(t, PLAYER_BADGE_STYLES.get(t, "1;37")) for t in tokens)
                else:
                    formatted = "".join(paint(t[-1], PLAYER_BADGE_STYLES.get(t, "1;37")) for t in tokens) + "  "
            elif sq == 100:
                formatted = paint(" ★100 ", "1;33;41")
            elif sq in LADDERS:
                dest = LADDERS[sq]
                txt = f" L{dest:<3d} " if dest == 100 else f" L{dest:<2d}  "
                formatted = paint(txt, "1;32")
            elif sq in SNAKES:
                dest = SNAKES[sq]
                txt = f" S{dest:<2d}  "
                formatted = paint(txt, "1;31")
            else:
                formatted = paint(f"  {sq:<2d}  ", "2")

            row_cells.append(formatted)

        rows.append("  │" + "│".join(row_cells) + "│")
        if r > 1:
            rows.append(mid_b)
        else:
            rows.append(bot_b)

    return "\n".join(rows)


def render_dashboard(view):
    players = view.get("players", [])
    raw_positions = view.get("positions", {})
    positions = {int(k): v for k, v in raw_positions.items()} if isinstance(raw_positions, dict) else {}
    turn_id = view.get("turn_id")
    last_roll = view.get("last_roll")
    last_movement = view.get("last_movement")
    log = view.get("log", [])

    out = [
        paint("=" * 73, "1;36"),
        paint("               🐍 S N A K E   &   L A D D E R S 🪜  (1–100)", "1;36"),
        paint("=" * 73, "1;36"),
        "",
        _render_board_grid(positions, players, last_movement),
        "",
        "  Legend: " + paint("L##", "1;32") + " = Ladder climbs to ##  |  " +
        paint("S##", "1;31") + " = Snake slides to ##  |  " +
        paint("★100", "1;33") + " = Winning Goal",
        ""
    ]

    # Trajectory / Movement Banner
    if last_movement:
        p_name = last_movement.get("player_name", "Player")
        roll = last_movement.get("roll", 0)
        from_sq = last_movement.get("from_sq", 1)
        rolled_to = last_movement.get("rolled_to", 1)
        final_sq = last_movement.get("final_sq", 1)
        m_type = last_movement.get("type", "normal")

        out.append(paint("  " + "─" * 69, "2"))
        if m_type == "ladder":
            ladder_to = last_movement.get("ladder_to", final_sq)
            out.append(
                paint(f"  🎲 LATEST MOVE: {p_name} rolled 🎲 {roll}!", "1;33") +
                f"\n     Square {from_sq} ──(+{roll})──> Square {rolled_to} ──" +
                paint(f"[🪜 LADDER CLIMB]──> Square {ladder_to}!", "1;32")
            )
        elif m_type == "snake":
            snake_to = last_movement.get("snake_to", final_sq)
            out.append(
                paint(f"  🎲 LATEST MOVE: {p_name} rolled 🎲 {roll}!", "1;33") +
                f"\n     Square {from_sq} ──(+{roll})──> Square {rolled_to} ──" +
                paint(f"[🐍 SNAKE SLIDE]──> Square {snake_to}!", "1;31")
            )
        elif m_type == "overshoot":
            out.append(
                paint(f"  🎲 LATEST MOVE: {p_name} rolled 🎲 {roll}!", "1;33") +
                f"\n     Square {from_sq} ──(+{roll})──> " +
                paint(f"Overshot 100! (Must roll exact). Stays at Square {from_sq}.", "1;31")
            )
        else:
            out.append(
                paint(f"  🎲 LATEST MOVE: {p_name} rolled 🎲 {roll}!", "1;33") +
                f"\n     Square {from_sq} ──(+{roll})──> Square {final_sq}"
            )
        out.append(paint("  " + "─" * 69, "2"))
        out.append("")

    out.append("  PLAYER POSITIONS & PROGRESS:")
    for p in players:
        pid = p["id"]
        pos = positions.get(pid, 1)
        color = p.get("color", "1;37")
        tok = p.get("token", f"P{pid + 1}")
        is_turn = (pid == turn_id)
        ptr = paint("▶", "1;32") if is_turn else " "
        tok_styled = paint(f"[{tok}]", color)
        steps_left = 100 - pos

        status_tag = ""
        if pos == 100:
            status_tag = " " + paint("🏆 WINNER!", "1;32")
        elif is_turn:
            status_tag = " " + paint("◀ CURRENT TURN", "1;36")

        out.append(f"   {ptr} {tok_styled} {p['name']:<18} : Square {pos:3d} / 100  ({steps_left:2d} steps to finish){status_tag}")

    if log:
        out.append("")
        out.append("  Recent activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
