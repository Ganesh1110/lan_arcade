"""
Mini Crossword Race Game Module.
2-Player Head-to-Head Crossword Sprint with Multi-Theme Puzzle Catalog.
"""
import random
from config import paint

game_id = "mini_crossword"
game_name = "Mini Crossword"
min_players = 2
max_players = 2

GRID_SIZE = 5

PUZZLES = [
    {
        "theme": "Everyday Tech & Nature",
        "grid": ["APPLE", "LOGIC", "SMART", "CODES", "TRAIN"],
        "clues": {
            "1A": ("Row 1 (5 letters)", "Red orchard fruit or tech giant", "APPLE"),
            "2A": ("Row 2 (5 letters)", "Reasoning principles or boolean gates", "LOGIC"),
            "3A": ("Row 3 (5 letters)", "Clever and quick-witted", "SMART"),
            "4A": ("Row 4 (5 letters)", "Written programs or secret ciphers", "CODES"),
            "5A": ("Row 5 (5 letters)", "Locomotive on railway tracks", "TRAIN")
        }
    },
    {
        "theme": "Space & Cosmic Elements",
        "grid": ["SOLAR", "ORBIT", "COMET", "EARTH", "SPACE"],
        "clues": {
            "1A": ("Row 1 (5 letters)", "Pertaining to our sun or radiation", "SOLAR"),
            "2A": ("Row 2 (5 letters)", "Curved gravitational path of a planet", "ORBIT"),
            "3A": ("Row 3 (5 letters)", "Icy celestial body with a glowing tail", "COMET"),
            "4A": ("Row 4 (5 letters)", "Our home blue marble planet", "EARTH"),
            "5A": ("Row 5 (5 letters)", "The infinite final frontier", "SPACE")
        }
    },
    {
        "theme": "Ocean & Wilderness",
        "grid": ["OCEAN", "CORAL", "TIGER", "RIVER", "BEACH"],
        "clues": {
            "1A": ("Row 1 (5 letters)", "Vast body of saltwater covering Earth", "OCEAN"),
            "2A": ("Row 2 (5 letters)", "Marine reef-building invertebrate colony", "CORAL"),
            "3A": ("Row 3 (5 letters)", "Striped apex jungle feline", "TIGER"),
            "4A": ("Row 4 (5 letters)", "Flowing freshwater natural stream", "RIVER"),
            "5A": ("Row 5 (5 letters)", "Sandy coastal strip by the waves", "BEACH")
        }
    },
    {
        "theme": "College & Campus Life",
        "grid": ["BOOKS", "STUDY", "GRADE", "LEARN", "CLASS"],
        "clues": {
            "1A": ("Row 1 (5 letters)", "Bound pages in the university library", "BOOKS"),
            "2A": ("Row 2 (5 letters)", "Review materials before midterms", "STUDY"),
            "3A": ("Row 3 (5 letters)", "Letter mark from A to F on an exam", "GRADE"),
            "4A": ("Row 4 (5 letters)", "Acquire new knowledge or skill", "LEARN"),
            "5A": ("Row 5 (5 letters)", "Lecture session in a hall", "CLASS")
        }
    }
]

# Legacy fallback for backwards compatibility
CLUES_ACROSS = PUZZLES[0]["clues"]


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

    puzzle_choice = random.choice(PUZZLES)

    return {
        "players": players,
        "boards": boards,
        "solved_counts": solved_counts,
        "puzzle": puzzle_choice,
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
    puzzle = state.get("puzzle", PUZZLES[0])

    # Sanitize clues so answers aren't exposed in network payload
    public_clues = {
        k: (desc, clue_text)
        for k, (desc, clue_text, _) in puzzle["clues"].items()
    }

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "theme": puzzle["theme"],
        "clues": public_clues,
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

    # Validate clue against active puzzle or fallback
    puzzle = state_or_view.get("puzzle")
    clues_map = puzzle["clues"] if puzzle else state_or_view.get("clues", CLUES_ACROSS)

    if clue not in clues_map:
        return False, f"Invalid clue '{clue}'. Choose from 1A to 5A."

    if len(word) != 5 or not word.isalpha():
        return False, "Word must be 5 letters long."

    return True, {"clue": clue, "word": word}


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    clue, word = action["clue"], action["word"]
    row_idx = int(clue[0]) - 1

    puzzle = state.get("puzzle", PUZZLES[0])
    expected_word = puzzle["clues"][clue][2]
    log_entries = []

    if word == expected_word:
        # Fill row on player's board
        for c in range(GRID_SIZE):
            state["boards"][player_id][row_idx][c] = word[c]

        # Calculate solved rows
        solved = sum(
            1 for r in range(GRID_SIZE)
            if "".join(state["boards"][player_id][r]) == puzzle["grid"][r]
        )
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
    return state["winner"] is not None or any(c == GRID_SIZE for c in state["solved_counts"].values())


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
    theme = view.get("theme", "Everyday Tech & Nature")
    clues = view.get("clues", {})
    log = view.get("log", [])

    out = [
        paint("=" * 56, "1;36"),
        paint("         M I N I   C R O S S W O R D   R A C E", "1;36"),
        paint(f"         Theme: {theme}", "1;33"),
        paint("=" * 56, "1;36"),
        "",
        f"  Your Progress: {paint(f'{my_solved}/5 solved', '1;32')}    Opponent ({opp_name}): {opp_solved}/5",
        "",
        "  YOUR GRID:"
    ]

    top_b = "       ┌───┬───┬───┬───┬───┐"
    mid_b = "       ├───┼───┼───┼───┼───┤"
    bot_b = "       └───┴───┴───┴───┴───┘"

    out.append(top_b)
    for r in range(GRID_SIZE):
        row_str = [f"    {r + 1}A │"]
        for c in range(GRID_SIZE):
            val = my_board[r][c]
            if val != ".":
                row_str.append(paint(f" {val} ", "1;32") + "│")
            else:
                row_str.append(paint(" · ", "2") + "│")
        out.append("".join(row_str))
        if r < GRID_SIZE - 1:
            out.append(mid_b)
        else:
            out.append(bot_b)

    out.append("")
    out.append("  CLUES (ACROSS):")
    if clues:
        for clue_id, clue_info in sorted(clues.items()):
            desc = clue_info[0] if isinstance(clue_info, (list, tuple)) else ""
            txt = clue_info[1] if isinstance(clue_info, (list, tuple)) and len(clue_info) > 1 else str(clue_info)
            out.append(f"   {paint(clue_id, '1;36')}: {txt} ({desc})")
    else:
        for clue_id, (desc, txt, _) in sorted(CLUES_ACROSS.items()):
            out.append(f"   {paint(clue_id, '1;36')}: {txt} ({desc})")

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
