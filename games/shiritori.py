"""
Word Chain / Shiritori Game Module.
2–4 Player Word Association Game with 3 Lives per player and English Dictionary Validation.
"""
from config import paint
from utils.dictionary import is_valid_word

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
        lives[pid] = 3  # 3 lives per player

    return {
        "players": players,
        "lives": lives,
        "used_words": set(),
        "last_word": None,
        "required_letter": None,
        "turn_index": 0,
        "winner": None,
        "log": ["🔤 Word Chain started! Form a chain of words."]
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
        "used_words": list(state["used_words"]),
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state.get("log", [])
    }


def prompt_for(state_or_view, player_id):
    req = state_or_view.get("required_letter")
    if req:
        return f"Enter word starting with '{req}' (or 'pass' to forfeit 1 life)"
    return "Enter any starting word (min 2 letters, or 'pass')"


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip().upper()
    if text in {"PASS", "SKIP"}:
        return True, "PASS"

    if not text or not text.isalpha() or len(text) < 2:
        return False, "Word must contain at least 2 letters (A–Z) or 'pass'."
    return True, text


def apply_action(state, player_id, word):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    p_name = curr_p["name"]
    log_entries = []

    req = state["required_letter"]
    used = state["used_words"]

    actives_before = active_players(state)
    curr_active_idx = next((i for i, p in enumerate(actives_before) if p["id"] == player_id), 0)

    if word == "PASS":
        state["lives"][player_id] -= 1
        rem = state["lives"][player_id]
        if rem > 0:
            log_entries.append(f"🏳️ {p_name} passed the turn → Forfeited 1 Life! ({rem} ❤️ left)")
        else:
            log_entries.append(f"💀 {p_name} passed the turn with 0 Lives left! ELIMINATED!")
    elif req and not word.startswith(req):
        state["lives"][player_id] -= 1
        rem = state["lives"][player_id]
        if rem > 0:
            log_entries.append(
                f"❌ {p_name} played '{word}' (Wrong starting letter! Required '{req}') → Lost 1 Life! ({rem} ❤️ left)"
            )
        else:
            log_entries.append(
                f"💀 {p_name} played '{word}' (Wrong starting letter! Required '{req}') → 0 Lives left! ELIMINATED!"
            )
    elif word in used:
        state["lives"][player_id] -= 1
        rem = state["lives"][player_id]
        if rem > 0:
            log_entries.append(
                f"❌ {p_name} played '{word}' (Already used word!) → Lost 1 Life! ({rem} ❤️ left)"
            )
        else:
            log_entries.append(
                f"💀 {p_name} played '{word}' (Already used word!) → 0 Lives left! ELIMINATED!"
            )
    elif not is_valid_word(word):
        state["lives"][player_id] -= 1
        rem = state["lives"][player_id]
        if rem > 0:
            log_entries.append(
                f"❌ {p_name} played '{word}' (Not in English dictionary!) → Lost 1 Life! ({rem} ❤️ left)"
            )
        else:
            log_entries.append(
                f"💀 {p_name} played '{word}' (Not in English dictionary!) → 0 Lives left! ELIMINATED!"
            )
    else:
        state["used_words"].add(word)
        state["last_word"] = word
        state["required_letter"] = word[-1]
        log_entries.append(f"🔤 {p_name} played '{word}' → Next word must start with '{word[-1]}'")

    # Advance turn order: if player was eliminated, do not skip the next active player
    was_eliminated = (state["lives"][player_id] <= 0)
    actives_after = active_players(state)

    if was_eliminated and actives_after:
        state["turn_index"] = curr_active_idx % len(actives_after)
    else:
        state["turn_index"] += 1

    actives = active_players(state)
    if len(actives) == 1:
        state["winner"] = [actives[0]["name"]]
        log_entries.append(f"🏆 {actives[0]['name']} is the last surviving player and WINS!")

    state.setdefault("log", []).extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

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
        actives = active_players(state)
        curr_idx = next((i for i, p in enumerate(actives) if p["id"] == player_id), 0)
        state["lives"][player_id] = 0
        new_actives = active_players(state)
        if new_actives:
            state["turn_index"] = curr_idx % len(new_actives)


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
        out.extend("   " + line for line in log[-6:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Game ended.", "1;33"))
    return "\n".join(parts)
