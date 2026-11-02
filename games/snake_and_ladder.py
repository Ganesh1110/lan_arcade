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
    1: 38,
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

    if curr_pos + roll > 100:
        log_entries.append(
            f"🎲 {p_name} rolled a {roll}! Overshoot! Needs exact roll to reach 100. Stays at Square {curr_pos}."
        )
        state["turn_index"] += 1
    else:
        new_pos = curr_pos + roll
        log_entries.append(f"🎲 {p_name} rolled a {roll}! Moved from Square {curr_pos} to {new_pos}.")

        if new_pos in LADDERS:
            dest = LADDERS[new_pos]
            log_entries.append(f"🪜 LADDER! {p_name} climbed from Square {new_pos} up to {dest}!")
            new_pos = dest
        elif new_pos in SNAKES:
            dest = SNAKES[new_pos]
            log_entries.append(f"🐍 SNAKE! {p_name} slid down from Square {new_pos} to {dest}!")
            new_pos = dest

        state["positions"][player_id] = new_pos

        if new_pos == 100:
            state["winner"] = [p_name]
            log_entries.append(f"🎉 {p_name} reached Square 100 and WINS the game!")
        elif roll == 6:
            log_entries.append(f"🔥 {p_name} rolled a 6 and gets an EXTRA TURN!")
            # Turn index remains same
        else:
            state["turn_index"] += 1

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


def _render_board_grid(positions, players):
    # Map square number to tokens present
    sq_tokens = {}
    for p in players:
        pid = p["id"]
        token = p["token"]
        pos = positions.get(pid, 1)
        sq_tokens.setdefault(pos, []).append(token)

    rows = []
    rows.append("  " + "+-----" * 10 + "+")

    for r in range(10, 0, -1):
        row_cells = []
        if r % 2 == 0:
            squares = list(range(r * 10, (r - 1) * 10, -1))
        else:
            squares = list(range((r - 1) * 10 + 1, r * 10 + 1))

        for sq in squares:
            tokens = sq_tokens.get(sq, [])
            if tokens:
                cell_str = ",".join(tokens)
                if len(cell_str) > 5:
                    cell_str = cell_str[:5]
                formatted = paint(f"{cell_str:^5}", "1;33")
            elif sq in LADDERS:
                formatted = paint(f"L{LADDERS[sq]:<2}  ", "1;32")
            elif sq in SNAKES:
                formatted = paint(f"S{SNAKES[sq]:<2}  ", "1;31")
            else:
                formatted = f"{sq:^5}"

            row_cells.append(formatted)

        rows.append("  | " + " | ".join(row_cells) + " |")
        rows.append("  " + "+-----" * 10 + "+")

    return "\n".join(rows)


def render_dashboard(view):
    players = view.get("players", [])
    positions = view.get("positions", {})
    turn_id = view.get("turn_id")
    last_roll = view.get("last_roll")
    log = view.get("log", [])

    out = [
        paint("=" * 66, "1;36"),
        paint("          S N A K E   &   L A D D E R S   (1–100)", "1;36"),
        paint("=" * 66, "1;36"),
        "",
        _render_board_grid(positions, players),
        "",
        "  Legend: " + paint("L##", "1;32") + " = Ladder Up to ##  |  " + paint("S##", "1;31") + " = Snake Down to ##",
        "",
        "  PLAYER POSITIONS:"
    ]

    for p in players:
        pid = p["id"]
        pos = positions.get(pid, 1)
        color = p.get("color", "1;37")
        ptr = paint("▶", color) if pid == turn_id else " "
        tok = paint(f"[{p['token']}]", color)
        out.append(f"   {ptr} {tok} {p['name']:<18} : Square {pos:3d}")

    if last_roll:
        out.append("")
        out.append(paint(f"  Last Dice Roll: 🎲 {last_roll}", "1;33"))

    if log:
        out.append("")
        out.append("  Recent activity:")
        out.extend("   " + line for line in log[-4:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
