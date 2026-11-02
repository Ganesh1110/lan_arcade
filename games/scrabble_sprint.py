"""
Anagram Showdown / Scrabble Sprint Game Module.
2–4 Player Speed Anagram Race with English Dictionary Validation and Reroll Mechanics.
"""
import random
from collections import Counter
from config import paint
from utils.dictionary import is_valid_word

game_id = "scrabble_sprint"
game_name = "Anagram Showdown"
min_players = 2
max_players = 4

SEED_WORDS = [
    "STREAM", "PLANET", "GARDEN", "MASTER", "SILVER", "SPRING",
    "CASTLE", "FROZEN", "WINTER", "FOREST", "DETAIL", "LISTEN",
    "PRINTER", "STUDENT", "CAPTURE", "WEATHER", "NETWORK", "COLLEGE"
]
EXTRA_LETTERS = "AEIOURSTLN"


def generate_rack():
    seed = list(random.choice(SEED_WORDS))
    # Add 1 extra common vowel/consonant to ensure 7-8 letters
    if len(seed) < 7:
        seed.append(random.choice(EXTRA_LETTERS))
    random.shuffle(seed)
    return seed


def create_state(player_sessions):
    players = []
    claimed = {}
    scores = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        claimed[pid] = set()
        scores[pid] = 0

    return {
        "players": players,
        "rack": generate_rack(),
        "claimed": claimed,
        "scores": scores,
        "all_claimed": set(),
        "consecutive_passes": 0,
        "turn_index": 0,
        "winner": None
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    my_words = list(state["claimed"].get(player_id, set()))

    summary = [
        {
            "id": p["id"],
            "name": p["name"],
            "score": state["scores"][p["id"]],
            "count": len(state["claimed"][p["id"]])
        }
        for p in state["players"]
    ]

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "rack": state["rack"],
        "my_words": sorted(my_words),
        "summary": summary,
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter anagram word (min 3 letters), 'pass', or 'reroll'"


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip().upper()
    if text in {"PASS", "SKIP"}:
        return True, "PASS"
    if text in {"REROLL", "SWAP"}:
        return True, "REROLL"

    word = text
    if len(word) < 3:
        return False, "Word must be at least 3 letters long (or 'pass' / 'reroll')."

    if not word.isalpha():
        return False, "Word must contain letters only."

    if not is_valid_word(word):
        return False, f"'{word}' is not recognized as a valid English word!"

    rack = state_or_view.get("rack", [])
    rack_counts = Counter(rack)
    word_counts = Counter(word)

    for ch, cnt in word_counts.items():
        if rack_counts[ch] < cnt:
            return False, f"Letter '{ch}' is not available in required quantity on your rack!"

    all_claimed = state_or_view.get("all_claimed", set())
    if isinstance(all_claimed, list):
        all_claimed = set(all_claimed)

    if word in all_claimed:
        return False, f"Word '{word}' was already claimed!"

    return True, word


def calc_score(word):
    l = len(word)
    if l == 3:
        return 3
    if l == 4:
        return 4
    if l == 5:
        return 6
    if l == 6:
        return 8
    return 15  # 7+ letter anagram bonus!


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    log_entries = []

    if action == "PASS":
        state["consecutive_passes"] = state.get("consecutive_passes", 0) + 1
        log_entries.append(
            f"⏩ {curr_p['name']} passed their turn ({state['consecutive_passes']}/{len(state['players'])} passes)."
        )
        if state["consecutive_passes"] >= len(state["players"]):
            max_s = max(state["scores"].values()) if state["scores"] else 0
            winners = [p["name"] for p in state["players"] if state["scores"][p["id"]] == max_s]
            state["winner"] = winners
            log_entries.append(f"🏁 All players passed! Game ended! Winner(s): {', '.join(winners)}.")
        state["turn_index"] += 1
        return {"log": log_entries}

    if action == "REROLL":
        state["rack"] = generate_rack()
        state["consecutive_passes"] = 0
        log_entries.append(f"🎲 {curr_p['name']} rerolled the letter rack! New letters drawn.")
        state["turn_index"] += 1
        return {"log": log_entries}

    word = action
    pts = calc_score(word)
    state["consecutive_passes"] = 0

    state["claimed"][player_id].add(word)
    state["all_claimed"].add(word)
    state["scores"][player_id] += pts

    log_entries.append(
        f"🔤 {curr_p['name']} submitted anagram '{word}' (+{pts} pts)! Total: {state['scores'][player_id]} pts."
    )

    if state["scores"][player_id] >= 20:
        state["winner"] = [curr_p["name"]]
        log_entries.append(f"🏆 {curr_p['name']} reached 20 points and WINS ANAGRAM SHOWDOWN!")

    state["turn_index"] += 1
    return {"log": log_entries}


def is_over(state):
    return (
        state["winner"] is not None
        or any(s >= 20 for s in state["scores"].values())
        or state.get("consecutive_passes", 0) >= len(state["players"])
    )


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    max_s = max(state["scores"].values()) if state["scores"] else 0
    return [p["name"] for p in state["players"] if state["scores"][p["id"]] == max_s]


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    rack = view.get("rack", [])
    my_words = view.get("my_words", [])
    summary = view.get("summary", [])
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("        A N A G R A M   S H O W D O W N", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        "  LETTER RACK: " + " ".join(paint(f"[{ch}]", "1;33") for ch in rack),
        "",
        f"  Your Words ({len(my_words)}): " + (", ".join(my_words) if my_words else "None"),
        "",
        "  SCOREBOARD (Target: 20 pts):"
    ]

    for p in summary:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        out.append(f"   {ptr} {p['name']:<20} Score: {p['score']} pts")

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
