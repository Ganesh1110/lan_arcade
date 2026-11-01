"""
Number Duel (High-Low) Game Module.
2–4 Player Deductive Number Guessing Game.
"""
import random
from config import paint

game_id = "number_duel"
game_name = "Number Duel (High-Low)"
min_players = 2
max_players = 4


def create_state(player_sessions):
    players = []
    scores = {}
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        scores[pid] = 0

    return {
        "players": players,
        "scores": scores,
        "secret_number": random.randint(1, 100),
        "min_range": 1,
        "max_range": 100,
        "turn_index": 0,
        "guesses_count": 0,
        "winner": None
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
        "scores": state["scores"],
        "min_range": state["min_range"],
        "max_range": state["max_range"],
        "guesses_count": state["guesses_count"],
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    mn = state_or_view.get("min_range", 1)
    mx = state_or_view.get("max_range", 100)
    return f"Enter guess between {mn} and {mx}"


def parse_action(state_or_view, player_id, raw_input):
    try:
        val = int(str(raw_input).strip())
    except (ValueError, TypeError):
        return False, "Enter a valid integer between 1 and 100."

    mn = state_or_view.get("min_range", 1)
    mx = state_or_view.get("max_range", 100)

    if not 1 <= val <= 100:
        return False, "Guess must be between 1 and 100."

    if val < mn or val > mx:
        return False, f"Guess {val} is outside current narrowed range [{mn}–{mx}]!"

    return True, val


def apply_action(state, player_id, guess):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    secret = state["secret_number"]
    state["guesses_count"] += 1
    log_entries = []

    if guess == secret:
        state["scores"][player_id] += 1
        state["winner"] = [curr_p["name"]]
        log_entries.append(f"🎉 {curr_p['name']} guessed EXACT NUMBER {secret} in {state['guesses_count']} total attempts and WINS!")
    elif guess < secret:
        state["min_range"] = max(state["min_range"], guess + 1)
        log_entries.append(f"⬆️ {curr_p['name']} guessed {guess} → HIGHER! Range is now [{state['min_range']}–{state['max_range']}]")
        state["turn_index"] += 1
    else:
        state["max_range"] = min(state["max_range"], guess - 1)
        log_entries.append(f"⬇️ {curr_p['name']} guessed {guess} → LOWER! Range is now [{state['min_range']}–{state['max_range']}]")
        state["turn_index"] += 1

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


def render_dashboard(view):
    players = view.get("players", [])
    mn = view.get("min_range", 1)
    mx = view.get("max_range", 100)
    cnt = view.get("guesses_count", 0)
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("         N U M B E R   D U E L   (1–100)", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        f"  Target Range: " + paint(f"[{mn} – {mx}]", "1;33") + f"   Total Attempts: {cnt}",
        "",
        "  PLAYERS:"
    ]

    for p in players:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        out.append(f"   {ptr} {p['name']:<20}")

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
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
