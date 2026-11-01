"""
Word Chain / Shiritori Game Module.
2–4 Player Word Association Game.
"""
from config import paint

game_id = "shiritori"
game_name = "Word Chain (Shiritori)"
min_players = 2
max_players = 4


def create_state(player_sessions):
    players = []
    lives = {}
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        lives[pid] = 3  # 3 strikes per player

    return {
        "players": players,
        "lives": lives,
        "used_words": set(),
        "last_word": None,
        "required_letter": None,
        "turn_index": 0,
        "winner": None
    }


def active_players(state):
    return [p for p in state["players"] if state["lives"][p["id"]] > 0]


def current_player(state):
    actives = active_players(state)
    if not actives:
        return state["players"][0]["id"]
    return actives[state["turn_index"] % len(actives)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    summary = [
        {
            "id": p["id"],
            "name": p["name"],
            "lives": state["lives"][p["id"]]
        }
        for p in state["players"]
    ]

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "summary": summary,
        "last_word": state["last_word"],
        "required_letter": state["required_letter"],
        "used_count": len(state["used_words"]),
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    req = state_or_view.get("required_letter")
    if req:
        return f"Enter word starting with '{req}'"
    return "Enter any starting word (min 2 letters)"


def parse_action(state_or_view, player_id, raw_input):
    word = str(raw_input).strip().upper()
    if not word or not word.isalpha() or len(word) < 2:
        return False, "Word must contain at least 2 letters (A–Z)."

    used = state_or_view.get("used_words", set())
    if isinstance(used, list):
        used = set(used)

    req = state_or_view.get("required_letter")
    if req and not word.startswith(req):
        return False, f"Word MUST start with the letter '{req}'!"

    if word in used:
        return False, f"The word '{word}' was already used in this match!"

    return True, word


def apply_action(state, player_id, word):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    log_entries = []

    state["used_words"].add(word)
    state["last_word"] = word
    state["required_letter"] = word[-1]

    log_entries.append(f"🔤 {curr_p['name']} played '{word}' → Next word must start with '{word[-1]}'")

    actives = active_players(state)
    if len(actives) == 1:
        state["winner"] = [actives[0]["name"]]
        log_entries.append(f"🏆 {actives[0]['name']} is the last surviving player and WINS!")
    else:
        state["turn_index"] += 1

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or len(active_players(state)) <= 1


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    actives = active_players(state)
    if len(actives) == 1:
        return [actives[0]["name"]]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["lives"][player_id] = 0
        state["turn_index"] += 1


def render_dashboard(view):
    summary = view.get("summary", [])
    last_word = view.get("last_word")
    req_letter = view.get("required_letter")
    used_cnt = view.get("used_count", 0)
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("         W O R D   C H A I N   (Shiritori)", "1;36"),
        paint("=" * 48, "1;36"),
        ""
    ]

    if last_word and req_letter:
        out.append(f"  Last Word: " + paint(f"'{last_word}'", "1;32") +
                   f"   →   Next Letter Required: " + paint(f"'{req_letter}'", "1;33"))
    else:
        out.append("  Chain Status: " + paint("[ Waiting for first word... ]", "2"))

    out.append(f"  Total Words Played: {used_cnt}")
    out.append("")
    out.append("  PLAYERS:")
    for p in summary:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        lives_str = "❤️ " * p["lives"] if p["lives"] > 0 else paint("ELIMINATED", "31")
        out.append(f"   {ptr} {p['name']:<20} {lives_str}")

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
