"""
Typing Racer Game Module.
2–4 Player Competitive Speed & Accuracy Typing Grand Prix with Live Multi-Lane Racetrack.
Features a rich, dynamically randomized library of programming quotes, real code snippets,
sci-fi/gamer phrases, and procedural tech scenario generation so every race is fresh and unique.
"""
import random
import time
from config import paint

game_id = "typing_racer"
game_name = "Typing Racer"
min_players = 2
max_players = 4

# =====================================================================
# CURATED DYNAMIC SNIPPET LIBRARIES BY CATEGORY
# =====================================================================

DEV_QUOTES = [
    "Talk is cheap. Show me the code.",
    "First, solve the problem. Then, write the code.",
    "Simplicity is prerequisite for reliability.",
    "Deleted code is debugged code.",
    "Make it work, make it right, make it fast.",
    "Good code is its own best documentation.",
    "It is not a bug, it is an undocumented feature.",
    "Any fool can write code that computers understand.",
    "Before software can be reusable it must be usable.",
    "There are 10 types of people: those who get binary, and those who do not.",
    "Computers are fast; programmers keep them slow.",
    "Premature optimization is the root of all evil.",
    "Code never lies, comments sometimes do.",
    "The best error message is the one that never shows up.",
    "Walking on water and coding from a spec are easy if both are frozen."
]

CODE_SNIPPETS = [
    "def binary_search(arr, target):",
    "git commit -m \"Initial commit\"",
    "while True: break",
    "console.log(\"Hello, World!\");",
    "chmod +x script.sh && ./script.sh",
    "SELECT * FROM users WHERE active = 1;",
    "import random, time, sys",
    "const [data, setData] = useState(null);",
    "docker compose up --build -d",
    "curl -sSL https://arcade.lan | bash",
    "grep -rn \"FIXME\" src/ --color=auto",
    "if err != nil { return err }",
    "for key, val in mapping.items():",
    "fn main() -> Result<(), Box<dyn Error>>",
    "export PATH=\"$HOME/bin:$PATH\""
]

SCIFI_SNIPPETS = [
    "Stay hungry. Stay foolish.",
    "Life is short, use Python.",
    "The cake is a lie, but the code compiles.",
    "Wake up, Neo. The Matrix has you.",
    "All your base are belong to us.",
    "Houston, tranquility base here. The Eagle has landed.",
    "Do androids dream of electric sheep?",
    "I will be back... right after this git push.",
    "May the source be with you, always.",
    "Never send a human to do a machine job.",
    "In space, no one can hear you syntax error.",
    "There is no spoon, only pointers.",
    "Resistance is futile, you will be merged.",
    "I think, therefore I compile.",
    "To infinity and beyond the buffer limit!"
]

PROCEDURAL_TEMPLATES = [
    ("Deploying {adj} {noun} to {cloud} on port {port}.", {
        "adj": ["scalable", "serverless", "encrypted", "fault-tolerant", "replicated"],
        "noun": ["microservices", "websocket proxies", "API gateways", "Redis clusters"],
        "cloud": ["AWS cluster", "GCP Kubernetes", "Docker Swarm", "bare-metal Linux"],
        "port": ["8080", "50555", "3000", "9092", "443"]
    }),
    ("Querying {db} cluster: latency {ms}ms across {shards} shards.", {
        "db": ["PostgreSQL", "ClickHouse", "Cassandra", "MongoDB", "Redis"],
        "ms": ["1.4", "2.8", "0.6", "4.2", "0.9"],
        "shards": ["12", "16", "32", "64"]
    }),
    ("Optimizing {algo} algorithm for O({comp}) runtime.", {
        "algo": ["quicksort", "Dijkstra", "binary search", "merge sort"],
        "comp": ["n log n", "log n", "1", "n"]
    }),
    ("git checkout -b {branch} && git merge {target}", {
        "branch": ["feature/auth", "hotfix/v2", "refactor/core", "perf/speed"],
        "target": ["main", "origin/main", "staging", "production"]
    }),
    ("Releasing v{ver} build to {env} with zero downtime.", {
        "ver": ["2.4.0", "3.1.2", "1.9.8", "4.0.1"],
        "env": ["production", "staging", "canary", "edge servers"]
    }),
    ("Bypassing {sec} firewall: neural handshake at {ghz} GHz.", {
        "sec": ["quantum", "ICE", "biometric", "elliptic-curve"],
        "ghz": ["4.8", "5.2", "8.4", "12.0"]
    }),
    ("Calibrating quantum core: {pct}% flux containment nominal.", {
        "pct": ["99.8", "98.5", "99.9", "97.4"]
    })
]

# Combined master list preserving backward compatibility
TARGET_SNIPPETS = DEV_QUOTES + CODE_SNIPPETS + SCIFI_SNIPPETS

TRACK_LENGTH = 30  # Number of progress bar segments
WINNING_PROGRESS = 100

LANE_VEHICLES = ["🏎️", "🚗", "🚙", "🚀"]


def generate_procedural_snippet():
    """Generate a procedural technical sentence from templates."""
    tmpl, vals = random.choice(PROCEDURAL_TEMPLATES)
    return tmpl.format(**{k: random.choice(v) for k, v in vals.items()})


def generate_dynamic_snippets(count=12):
    """
    Generate a dynamic, diverse playlist of typing snippets for a race.
    Pulls from curated categories (programming quotes, real code snippets,
    sci-fi/gaming phrases, and procedurally generated tech scenarios),
    shuffling them so every single race is fresh, varied, and exciting.
    """
    selected = []
    # Sample from curated categories
    for cat_list in [DEV_QUOTES, CODE_SNIPPETS, SCIFI_SNIPPETS]:
        sample_size = min(len(cat_list), 3)
        selected.extend(random.sample(cat_list, sample_size))

    # Add procedural tech phrases
    procedural_count = max(2, count - len(selected))
    for _ in range(procedural_count):
        selected.append(generate_procedural_snippet())

    # Shuffle thoroughly
    random.shuffle(selected)
    return selected[:count]


def get_current_snippet(state):
    """Retrieve the active target snippet for the current turn."""
    snippets = state.get("snippets")
    if not snippets:
        snippets = TARGET_SNIPPETS
    snip_idx = state.get("snippet_index", 0) % len(snippets)
    return snippets[snip_idx]


def calculate_accuracy(expected, typed):
    """Calculate character accuracy percentage between expected and typed strings."""
    if not expected:
        return 100.0
    matches = sum(1 for e, t in zip(expected, typed) if e == t)
    return max(0.0, round((matches / max(len(expected), len(typed))) * 100.0, 1))


def create_state(player_sessions, snippets=None, randomize=True):
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

    if snippets is not None:
        race_snippets = list(snippets)
    elif randomize:
        race_snippets = generate_dynamic_snippets(12)
    else:
        race_snippets = list(TARGET_SNIPPETS)

    return {
        "players": players,
        "progress": progress,
        "wpm_records": wpm_records,
        "snippets": race_snippets,
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
    current_snippet = get_current_snippet(state)

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

    expected = get_current_snippet(state)

    acc = calculate_accuracy(expected, typed_text)
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

    # Display Target Typing Snippet in dynamic box
    box_w = 64
    inner_w = box_w - 4
    words_cnt = len(target_snip.split())
    chars_cnt = len(target_snip)
    stats_tag = f"({chars_cnt} chars • {words_cnt} words)"
    header_title = "TYPE THIS TARGET SNIPPET EXACTLY:"
    spacer_len = max(1, inner_w - len(header_title) - len(stats_tag))
    header_line = paint(header_title, "1;33") + (" " * spacer_len) + paint(stats_tag, "2;37")

    out.append("  " + paint("┌" + "─" * (box_w - 2) + "┐", "1;36"))
    out.append("  │ " + header_line + " │")
    out.append("  " + paint("├" + "─" * (box_w - 2) + "┤", "1;36"))

    if len(target_snip) <= inner_w:
        padded_snip = target_snip.ljust(inner_w)
        out.append("  │ " + paint(padded_snip, "1;32") + " │")
    else:
        # Wrap words across multiple lines cleanly
        words = target_snip.split()
        curr_line = ""
        for w in words:
            if not curr_line:
                curr_line = w
            elif len(curr_line) + 1 + len(w) <= inner_w:
                curr_line += " " + w
            else:
                out.append("  │ " + paint(curr_line.ljust(inner_w), "1;32") + " │")
                curr_line = w
        if curr_line:
            out.append("  │ " + paint(curr_line.ljust(inner_w), "1;32") + " │")

    out.append("  " + paint("└" + "─" * (box_w - 2) + "┘", "1;36"))

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

