"""
Mini Crossword Race Game Module.
2-Player Head-to-Head Crossword Sprint.
"""
from config import paint

game_id = "mini_crossword"
game_name = "Mini Crossword"
min_players = 2
max_players = 2

GRID_SIZE = 5

SOLUTION_GRID = [
    ["A", "P", "P", "L", "E"],
    ["L", "O", "G", "I", "C"],
    ["S", "M", "A", "R", "T"],
    ["C", "O", "D", "E", "S"],
    ["T", "R", "A", "I", "N"]
]

CLUES_ACROSS = {
    "1A": ("Row 1 (5 letters)", "Red delicious fruit", "APPLE"),
    "2A": ("Row 2 (5 letters)", "Reasoning or programming rules", "LOGIC"),
    "3A": ("Row 3 (5 letters)", "Clever and intelligent", "SMART"),
    "4A": ("Row 4 (5 letters)", "Written programs or ciphers", "CODES"),
    "5A": ("Row 5 (5 letters)", "Railway locomotive transport", "TRAIN")
}


def create_state(player_sessions):
    players = []
    boards = {}
    solved_counts = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        boards[pid] = [["."] * GRID_SIZE for _ in range(GRID_SIZE)]
        solved_counts[pid] = 0

    return {
        "players": players,
        "boards": boards,
        "solved_counts": solved_counts,
        "turn_index": 0,
        "winner": None
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    my_board = state["boards"].get(player_id, [["."] * GRID_SIZE for _ in range(GRID_SIZE)])
    opp_solved = state["solved_counts"].get(opp["id"], 0) if opp else 0

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "my_board": my_board,
        "my_solved": state["solved_counts"].get(player_id, 0),
        "opp_solved": opp_solved,
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter clue and word (e.g. '1A APPLE' or '3A SMART')"


def parse_action(state_or_view, player_id, raw_input):
    parts = str(raw_input).strip().upper().split()
    if len(parts) != 2:
        return False, "Format: '<clue_num> <word>' (e.g. '1A APPLE' or '3A SMART')."

    clue, word = parts[0], parts[1]
    if clue not in CLUES_ACROSS:
        return False, f"Invalid clue '{clue}'. Choose from 1A to 5A."

    if len(word) != 5 or not word.isalpha():
        return False, "Word must be 5 letters long."

    return True, {"clue": clue, "word": word}


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    clue, word = action["clue"], action["word"]
    row_idx = int(clue[0]) - 1

    expected_word = CLUES_ACROSS[clue][2]
    log_entries = []

    if word == expected_word:
        # Fill row on player's board
        for c in range(GRID_SIZE):
            state["boards"][player_id][row_idx][c] = word[c]

        # Calculate solved rows
        solved = sum(1 for r in range(GRID_SIZE) if "".join(state["boards"][player_id][r]) == "".join(SOLUTION_GRID[r]))
        state["solved_counts"][player_id] = solved

        log_entries.append(f"✨ {curr_p['name']} SOLVED {clue}: '{word}'! ({solved}/5 solved)")

        if solved == GRID_SIZE:
            state["winner"] = [curr_p["name"]]
            log_entries.append(f"🏆 {curr_p['name']} COMPLETED THE MINI CROSSWORD AND WINS!")
    else:
        log_entries.append(f"❌ {curr_p['name']} guessed '{word}' for {clue} — Incorrect!")

    state["turn_index"] += 1
    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or any(s >= 5 for s in state["solved_counts"].values())


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    max_s = max(state["solved_counts"].values()) if state["solved_counts"] else 0
    return [p["name"] for p in state["players"] if state["solved_counts"][p["id"]] == max_s]


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    name = view.get("name", "Player")
    opp_name = view.get("opponent_name", "Opponent")
    my_board = view.get("my_board", [["."] * GRID_SIZE for _ in range(GRID_SIZE)])
    my_solved = view.get("my_solved", 0)
    opp_solved = view.get("opp_solved", 0)
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("          M I N I   C R O S S W O R D", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        f"  You ({name}): {my_solved}/5 solved   vs   {opp_name}: {opp_solved}/5 solved",
        "",
        "  YOUR CROSSWORD BOARD:"
    ]

    border = "  +" + "---+" * GRID_SIZE
    out.append(border)
    for r in range(GRID_SIZE):
        row_str = [f"{r + 1} |"]
        for c in range(GRID_SIZE):
            v = my_board[r][c]
            cell = paint(f" {v} ", "1;32") if v != "." else " . "
            row_str.append(cell + "|")
        out.append("".join(row_str))
        out.append(border)

    out.append("")
    out.append("  ACROSS CLUES:")
    for key, (label, desc, _) in CLUES_ACROSS.items():
        out.append(f"   {key:<3} {desc:<32} ({label})")

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
