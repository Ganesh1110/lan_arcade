"""
Typing Racer Game Module.
2–4 Player Competitive Speed & Accuracy Typing Grand Prix with Live Multi-Lane Racetrack.
"""
import time
from config import paint

game_id = "typing_racer"
game_name = "Typing Racer"
min_players = 2
max_players = 4

TARGET_SNIPPETS = [
    "Talk is cheap. Show me the code.",
    "def binary_search(arr, target):",
    "git commit -m 'Initial commit'",
    "while True: break",
    "Stay hungry. Stay foolish.",
    "import random, time, sys",
    "console.log('Hello, World!');",
    "chmod +x script.sh && ./script.sh",
    "SELECT * FROM users WHERE active = 1;",
    "Life is short, use Python."
]

TRACK_LENGTH = 30  # Number of progress bar segments
WINNING_PROGRESS = 100

LANE_VEHICLES = ["🏎️", "🚗", "🚙", "🚀"]


def calculate_accuracy(expected, typed):
    """Calculate character accuracy percentage between expected and typed strings."""
    if not expected:
        return 100.0
    matches = sum(1 for e, t in zip(expected, typed) if e == t)
    return max(0.0, round((matches / max(len(expected), len(typed))) * 100.0, 1))


def create_state(player_sessions):
    players = []
    progress = {}
    wpm_records = {}

    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        veh = LANE_VEHICLES[idx % len(LANE_VEHICLES)]
        players.append({"id": pid, "name": name, "vehicle": veh, "lane": idx + 1})
        progress[pid] = 0
        wpm_records[pid] = 0

    return {
        "players": players,
        "progress": progress,
        "wpm_records": wpm_records,
        "snippet_index": 0,
        "turn_index": 0,
        "turn_start_time": time.time(),
        "winner": None,
        "log": ["🏎️ Welcome to Typing Racer! Type each snippet accurately to accelerate across the finish line!"]
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    snip_idx = state.get("snippet_index", 0) % len(TARGET_SNIPPETS)
    current_snippet = TARGET_SNIPPETS[snip_idx]

    # Normalize progress keys with integers
    raw_prog = state.get("progress", {})
    progress = {int(k): v for k, v in raw_prog.items()} if isinstance(raw_prog, dict) else {}
    raw_wpm = state.get("wpm_records", {})
    wpm = {int(k): v for k, v in raw_wpm.items()} if isinstance(raw_wpm, dict) else {}

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "players": state["players"],
        "progress": progress,
        "wpm_records": wpm,
        "target_snippet": current_snippet,
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Type the exact target snippet above and press [ENTER]"


def parse_action(state_or_view, player_id, raw_input):
    # Any typed string is valid input for the typing race
    return True, str(raw_input)


def apply_action(state, player_id, typed_text):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    p_name = curr_p["name"]

    snip_idx = state.get("snippet_index", 0) % len(TARGET_SNIPPETS)
    expected = TARGET_SNIPPETS[snip_idx]

    acc = calculate_accuracy(expected, typed_text)
    # Estimate WPM based on character count
    word_count = len(expected.split())
    gain = 0
    log_entries = []

    if acc >= 90.0:
        gain = 35
        state["progress"][player_id] = min(WINNING_PROGRESS, state["progress"].get(player_id, 0) + gain)
        log_entries.append(f"⚡ {p_name} typed with {acc}% accuracy! +{gain}% Nitro boost!")
    elif acc >= 60.0:
        gain = 20
        state["progress"][player_id] = min(WINNING_PROGRESS, state["progress"].get(player_id, 0) + gain)
        log_entries.append(f"🚗 {p_name} typed with {acc}% accuracy! +{gain}% forward move.")
    else:
        gain = 5
        state["progress"][player_id] = min(WINNING_PROGRESS, state["progress"].get(player_id, 0) + gain)
        log_entries.append(f"⚠️ {p_name} had typos ({acc}% accuracy). Stumbled forward +{gain}%.")

    if state["progress"][player_id] >= WINNING_PROGRESS:
        state["winner"] = [p_name]
        log_entries.append(f"🏁 {p_name} crossed the FINISH LINE and wins the Grand Prix!")

    state["snippet_index"] += 1
    state["turn_index"] += 1

    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or any(p >= WINNING_PROGRESS for p in state.get("progress", {}).values())


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    if is_over(state):
        max_prog = max(state.get("progress", {}).values())
        return [p["name"] for p in state["players"] if state["progress"].get(p["id"], 0) == max_prog]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["snippet_index"] += 1
        state["turn_index"] += 1


def render_dashboard(view):
    players = view.get("players", [])
    raw_prog = view.get("progress", {})
    progress = {int(k): v for k, v in raw_prog.items()} if isinstance(raw_prog, dict) else {}
    target_snip = view.get("target_snippet", "Hello World")
    turn_id = view.get("turn_id")
    my_id = view.get("player_id")
    log = view.get("log", [])

    out = [
        paint("=" * 66, "1;36"),
        paint("             🏎️  T Y P I N G   R A C E R   🏁", "1;36"),
        paint("=" * 66, "1;36"),
        "",
        "  RACETRACK (FINISH LINE AT 100%):"
    ]

    # Render each player's lane
    for p in players:
        pid = p["id"]
        prog = progress.get(pid, 0)
        veh = p.get("vehicle", "🏎️")
        p_name = p["name"]

        # Scale progress to TRACK_LENGTH characters
        fill = int((prog / WINNING_PROGRESS) * TRACK_LENGTH)
        fill = min(TRACK_LENGTH, max(0, fill))
        empty = TRACK_LENGTH - fill

        track_bar = paint("=" * fill, "1;32") + veh + paint("-" * empty, "2")
        is_turn = (pid == turn_id)
        ptr = paint("▶", "1;32") if is_turn else " "
        name_tag = paint(f"{p_name:<12}", "1;33") if pid == my_id else f"{p_name:<12}"

        out.append(f"  {ptr} Lane {p.get('lane', 1)}: [{name_tag}] |{track_bar}| {prog:3d}% 🏁")

    out.append("")

    # Display Target Typing Snippet in clear box
    out.append("  " + paint("┌" + "─" * 62 + "┐", "1;36"))
    out.append("  │ " + paint("TYPE THIS TARGET SNIPPET EXACTLY:", "1;33") + " " * 27 + "│")
    out.append("  " + paint("├" + "─" * 62 + "┤", "1;36"))
    out.append(f"  │  {paint(target_snip, '1;32'):<69}│")
    out.append("  " + paint("└" + "─" * 62 + "┘", "1;36"))

    if log:
        out.append("")
        out.append("  Race Activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  GRAND PRIX CHAMPION: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Race ended in a photo finish draw!", "1;33"))
    return "\n".join(parts)
