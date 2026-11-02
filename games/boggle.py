"""
Boggle / Word Hunt Game Module.
2–4 Player Word Search Grid Game with English Dictionary Validation and Pass Mechanics.
"""
import random
from config import paint
from utils.dictionary import is_valid_word

game_id = "boggle"
game_name = "Boggle / Word Hunt"
min_players = 2
max_players = 4

GRID_SIZE = 4
DICE = [
    "RIFHOB", "OUMHTC", "LNPEDO", "VIOTRE",
    "DECAMP", "IYSBPR", "TUSTOW", "NEHRIS",
    "GUEINK", "STIONA", "TOWTOA", "AWEMOR",
    "KAFFSC", "JXBQZO", "LEXVPZ", "YIDSTN"
]


def generate_boggle_grid():
    random.shuffle(DICE)
    grid = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            die = DICE[r * GRID_SIZE + c]
            row.append(random.choice(die))
        grid.append(row)
    return grid


def create_state(player_sessions):
    players = []
    found_words = {}
    scores = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        found_words[pid] = set()
        scores[pid] = 0

    return {
        "players": players,
        "grid": generate_boggle_grid(),
        "found_words": found_words,
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
    my_words = list(state["found_words"].get(player_id, set()))

    summary = [
        {
            "id": p["id"],
            "name": p["name"],
            "score": state["scores"][p["id"]],
            "count": len(state["found_words"][p["id"]])
        }
        for p in state["players"]
    ]

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "grid": state["grid"],
        "my_words": sorted(my_words),
        "my_score": state["scores"].get(player_id, 0),
        "summary": summary,
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Find & enter word from grid (min 3 letters) or 'pass'"


def is_word_in_grid(word, grid):
    # DFS search on 4x4 grid
    R, C = len(grid), len(grid[0])

    def dfs(r, c, idx, visited):
        if idx == len(word):
            return True
        if not (0 <= r < R and 0 <= c < C) or (r, c) in visited:
            return False
        if grid[r][c] != word[idx]:
            return False

        visited.add((r, c))
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr != 0 or dc != 0:
                    if dfs(r + dr, c + dc, idx + 1, visited):
                        return True
        visited.remove((r, c))
        return False

    for r in range(R):
        for c in range(C):
            if dfs(r, c, 0, set()):
                return True
    return False


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip().upper()
    if text in {"PASS", "SKIP"}:
        return True, "PASS"

    word = text
    if len(word) < 3:
        return False, "Word must be at least 3 letters long (or 'pass')."

    if not word.isalpha():
        return False, "Word must contain only letters."

    if not is_valid_word(word):
        return False, f"'{word}' is not recognized as a valid English word!"

    grid = state_or_view.get("grid", [])
    if grid and not is_word_in_grid(word, grid):
        return False, f"Word '{word}' cannot be formed by adjacent letters on the board!"

    all_claimed = state_or_view.get("all_claimed", set())
    if isinstance(all_claimed, list):
        all_claimed = set(all_claimed)

    if word in all_claimed:
        return False, f"Word '{word}' was already claimed by a player!"

    return True, word


def calc_score(word):
    l = len(word)
    if l in [3, 4]:
        return 1
    if l == 5:
        return 2
    if l == 6:
        return 3
    return 5


def apply_action(state, player_id, word):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    log_entries = []

    if word == "PASS":
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

    state["consecutive_passes"] = 0
    pts = calc_score(word)

    state["found_words"][player_id].add(word)
    state["all_claimed"].add(word)
    state["scores"][player_id] += pts

    log_entries.append(f"🔤 {curr_p['name']} found '{word}' (+{pts} pts)! Total: {state['scores'][player_id]} pts.")

    # Win condition: First to reach 15 points
    if state["scores"][player_id] >= 15:
        state["winner"] = [curr_p["name"]]
        log_entries.append(f"🏆 {curr_p['name']} reached 15 points and WINS BOGGLE!")

    state["turn_index"] += 1
    return {"log": log_entries}


def is_over(state):
    return (
        state["winner"] is not None
        or any(s >= 15 for s in state["scores"].values())
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
    grid = view.get("grid", [["."] * GRID_SIZE for _ in range(GRID_SIZE)])
    my_words = view.get("my_words", [])
    my_score = view.get("my_score", 0)
    summary = view.get("summary", [])
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 52, "1;36"),
        paint("          B O G G L E   /   W O R D   H U N T", "1;36"),
        paint("=" * 52, "1;36"),
        "",
        "  4x4 LETTER GRID:"
    ]

    top_b = "        ┌─────┬─────┬─────┬─────┐"
    mid_b = "        ├─────┼─────┼─────┼─────┤"
    bot_b = "        └─────┴─────┴─────┴─────┘"

    out.append(top_b)
    for r in range(GRID_SIZE):
        row_str = ["        │"]
        for c in range(GRID_SIZE):
            ch = grid[r][c] if r < len(grid) and c < len(grid[r]) else "."
            row_str.append(paint(f"  {ch}  ", "1;33") + "│")
        out.append("".join(row_str))
        if r < GRID_SIZE - 1:
            out.append(mid_b)
        else:
            out.append(bot_b)

    out.append("")
    out.append(f"  Your Score: {paint(str(my_score) + ' pts', '1;32')} (Words: {', '.join(my_words) if my_words else 'None'})")
    out.append("")
    out.append("  PLAYERS:")
    for p in summary:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        out.append(f"   {ptr} {p['name']:<20} {p['score']} pts ({p['count']} words)")

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
