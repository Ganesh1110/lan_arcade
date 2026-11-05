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
        "theme": "Heart & Soul",
        "grid": ["HEART", "EMBER", "ABUSE", "RESIN", "TREND"],
        "clues": {
            "1A": ("Row 1", "Muscular pump in the chest or symbol of love", "HEART"),
            "2A": ("Row 2", "Glowing coal left behind in a dying hearth", "EMBER"),
            "3A": ("Row 3", "Misuse, improper treatment, or corrupt conduct", "ABUSE"),
            "4A": ("Row 4", "Sticky amber fluid secreted by pine trees", "RESIN"),
            "5A": ("Row 5", "General direction in which things are developing", "TREND"),
            "1D": ("Col 1", "Core vital organ that sustains human life", "HEART"),
            "2D": ("Col 2", "Smoldering fragment of hot charred wood", "EMBER"),
            "3D": ("Col 3", "Cruel or excessively harmful exploitation", "ABUSE"),
            "4D": ("Col 4", "Natural organic varnish and rosin polymer", "RESIN"),
            "5D": ("Col 5", "Viral craze or popular modern fashion", "TREND"),
        }
    },
    {
        "theme": "Wings & Wilderness",
        "grid": ["CRANE", "RIVAL", "AVOID", "NAIVE", "ELDER"],
        "clues": {
            "1A": ("Row 1", "Long-legged wading bird or harbor hoisting machine", "CRANE"),
            "2A": ("Row 2", "Fierce adversary or challenger in competition", "RIVAL"),
            "3A": ("Row 3", "Steer clear of, evade, or shun", "AVOID"),
            "4A": ("Row 4", "Innocent, gullible, or lacking worldly experience", "NAIVE"),
            "5A": ("Row 5", "Venerable senior member of a family or clan", "ELDER"),
            "1D": ("Col 1", "Tall mechanical derrick lifting construction loads", "CRANE"),
            "2D": ("Col 2", "Close opponent fighting for the same trophy", "RIVAL"),
            "3D": ("Col 3", "Stay away from or dodge neatly", "AVOID"),
            "4D": ("Col 4", "Showing lack of critical cynicism; ingenuous", "NAIVE"),
            "5D": ("Col 5", "Respected village patriarch or older shrub", "ELDER"),
        }
    },
    {
        "theme": "Logic & Discovery",
        "grid": ["SOLVE", "ONION", "LIMIT", "VOICE", "ENTER"],
        "clues": {
            "1A": ("Row 1", "Unravel a mystery or find the solution to a riddle", "SOLVE"),
            "2A": ("Row 2", "Pungent edible bulb that causes kitchen tears", "ONION"),
            "3A": ("Row 3", "Upper boundary, speed cap, or threshold", "LIMIT"),
            "4A": ("Row 4", "Sound emitted from vocal chords during speech", "VOICE"),
            "5A": ("Row 5", "Walk into a room, or key pressed to submit", "ENTER"),
            "1D": ("Col 1", "Crack an algorithmic problem or math equation", "SOLVE"),
            "2D": ("Col 2", "Layered root vegetable sautéed in savory soups", "ONION"),
            "3D": ("Col 3", "Maximum allowable measure or ceiling constraint", "LIMIT"),
            "4D": ("Col 4", "Singing tone or spoken expression", "VOICE"),
            "5D": ("Col 5", "Pass through a doorway into a chamber", "ENTER"),
        }
    },
    {
        "theme": "Campus & Energy",
        "grid": ["BLAST", "LUNCH", "ANGER", "SCENE", "THREE"],
        "clues": {
            "1A": ("Row 1", "Sudden loud explosion or intense sonic burst", "BLAST"),
            "2A": ("Row 2", "Midday cafeteria meal enjoyed with classmates", "LUNCH"),
            "3A": ("Row 3", "Intense feeling of wrath or sharp irritation", "ANGER"),
            "4A": ("Row 4", "Dramatic episode or view on a theater stage", "SCENE"),
            "5A": ("Row 5", "Number of sides on a geometric triangle", "THREE"),
            "1D": ("Col 1", "Powerful shockwave or fun energetic gathering", "BLAST"),
            "2D": ("Col 2", "Noontime sandwich break between classes", "LUNCH"),
            "3D": ("Col 3", "Furious emotional rage or indignant hostility", "ANGER"),
            "4D": ("Col 4", "Setting of an action or theatrical segment", "SCENE"),
            "5D": ("Col 5", "Smallest odd prime integer", "THREE"),
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
    return "Enter clue and word, e.g. Across '1A HEART' or Down '1D HEART'"


def parse_action(state_or_view, player_id, raw_input):
    parts = str(raw_input).strip().upper().split()
    if len(parts) != 2:
        return False, "Format: '<clue_num> <word>' (e.g. '1A HEART' or '1D HEART')."

    clue, word = parts[0], parts[1]

    # Validate clue against active puzzle or fallback
    puzzle = state_or_view.get("puzzle")
    clues_map = puzzle["clues"] if puzzle else state_or_view.get("clues", CLUES_ACROSS)

    if clue not in clues_map:
        return False, f"Invalid clue '{clue}'. Choose Across (1A–5A) or Down (1D–5D)."

    if len(word) != 5 or not word.isalpha():
        return False, "Word must be 5 letters long."

    return True, {"clue": clue, "word": word}


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    clue, word = action["clue"], action["word"]
    idx = int(clue[0]) - 1

    puzzle = state.get("puzzle", PUZZLES[0])
    expected_word = puzzle["clues"][clue][2]
    log_entries = []

    if word == expected_word:
        # Fill row (Across) or column (Down) on player's board
        if clue.endswith("A"):
            for c in range(GRID_SIZE):
                state["boards"][player_id][idx][c] = word[c]
        elif clue.endswith("D"):
            for r in range(GRID_SIZE):
                state["boards"][player_id][r][idx] = word[r]

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
    theme = view.get("theme", "Heart & Soul")
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

    col_hdr = "        1D  2D  3D  4D  5D"
    out.append(paint(col_hdr, "1;33"))
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
    all_clues = clues if clues else CLUES_ACROSS
    across_clues = {k: v for k, v in all_clues.items() if k.endswith("A")}
    down_clues = {k: v for k, v in all_clues.items() if k.endswith("D")}

    if across_clues:
        out.append("  CLUES (ACROSS):")
        for clue_id, clue_info in sorted(across_clues.items()):
            desc = clue_info[0] if isinstance(clue_info, (list, tuple)) else ""
            txt = clue_info[1] if isinstance(clue_info, (list, tuple)) and len(clue_info) > 1 else str(clue_info)
            out.append(f"   {paint(clue_id, '1;36')}: {txt} ({desc})")

    if down_clues:
        out.append("")
        out.append("  CLUES (DOWN):")
        for clue_id, clue_info in sorted(down_clues.items()):
            desc = clue_info[0] if isinstance(clue_info, (list, tuple)) else ""
            txt = clue_info[1] if isinstance(clue_info, (list, tuple)) and len(clue_info) > 1 else str(clue_info)
            out.append(f"   {paint(clue_id, '1;35')}: {txt} ({desc})")

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
