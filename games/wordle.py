"""
Wordle Versus Game Module.
2-Player Competitive 5-Letter Word Deduction Race with Live Dual Boards and Keyboard Tracking.
"""
import random
from config import paint
from utils.dictionary import is_valid_word

game_id = "wordle"
game_name = "Wordle Versus"
min_players = 2
max_players = 2

TARGET_WORDS = [
    "APPLE", "BEACH", "BRAVE", "CHAIR", "CLOUD", "CRANE", "DANCE", "DREAM",
    "EARTH", "FLAME", "FOCUS", "GHOST", "GRACE", "HEART", "HONEY", "HOUSE",
    "LIGHT", "MAGIC", "MUSIC", "NIGHT", "OCEAN", "PEACE", "PIANO", "PLANT",
    "PRIDE", "QUEEN", "RIVER", "SHINE", "SMILE", "SPARK", "STORM", "SUGAR",
    "TIGER", "TRAIN", "WATER", "WHITE", "WORLD", "YOUTH", "ZEBRA", "BREAD"
]

MAX_ATTEMPTS = 6


def evaluate_guess(target, guess):
    """
    Evaluate a 5-letter guess against the target word.
    Returns list of 5 tuples: (letter, status)
    where status is 'green', 'yellow', or 'gray'.
    """
    target = target.upper()
    guess = guess.upper()
    res = [None] * 5
    target_counts = {}

    # Pass 1: find greens (exact match)
    for i in range(5):
        if guess[i] == target[i]:
            res[i] = "green"
        else:
            target_counts[target[i]] = target_counts.get(target[i], 0) + 1

    # Pass 2: find yellows and grays
    for i in range(5):
        if res[i] is None:
            g_char = guess[i]
            if target_counts.get(g_char, 0) > 0:
                res[i] = "yellow"
                target_counts[g_char] -= 1
            else:
                res[i] = "gray"

    return list(zip(guess, res))


def create_state(player_sessions):
    players = []
    guesses = {}
    solved = {}

    target = random.choice(TARGET_WORDS)

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        guesses[pid] = []
        solved[pid] = False

    return {
        "players": players,
        "target_word": target,
        "guesses": guesses,
        "solved": solved,
        "turn_index": 0,
        "winner": None,
        "log": ["🟩 Wordle Versus match started! Deduce the 5-letter word in 6 tries."]
    }


def current_player(state):
    players = state["players"]
    # If a player has already solved or used 6 attempts, turn passes to opponent
    p0 = players[0]["id"]
    p1 = players[1]["id"]
    p0_done = state["solved"].get(p0, False) or len(state["guesses"].get(p0, [])) >= MAX_ATTEMPTS
    p1_done = state["solved"].get(p1, False) or len(state["guesses"].get(p1, [])) >= MAX_ATTEMPTS

    if p0_done and not p1_done:
        return p1
    if p1_done and not p0_done:
        return p0
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    my_guesses = state["guesses"].get(player_id, [])
    opp_guesses = state["guesses"].get(opp["id"], []) if opp else []

    # Opponent tiles are masked for privacy (only colors shown, not letters)
    masked_opp = []
    for g_eval in opp_guesses:
        masked_opp.append([("?", status) for _, status in g_eval])

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "my_guesses": my_guesses,
        "opp_guesses": masked_opp,
        "my_solved": state["solved"].get(player_id, False),
        "opp_solved": state["solved"].get(opp["id"], False) if opp else False,
        "turn_id": current_player(state),
        "winner": state["winner"],
        "log": state["log"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter any 5-letter English word (e.g. CRANE, GHOST)"


def parse_action(state_or_view, player_id, raw_input):
    word = str(raw_input).strip().upper()
    if len(word) != 5 or not word.isalpha():
        return False, f"Guess must be exactly 5 letters (A–Z), received '{word}'."

    # Validate against dictionary if available or target word list
    if not is_valid_word(word) and word not in TARGET_WORDS:
        return False, f"'{word}' is not in the recognized dictionary."

    return True, word


def apply_action(state, player_id, word):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    p_name = curr_p["name"]
    target = state["target_word"]

    eval_result = evaluate_guess(target, word)
    state["guesses"].setdefault(player_id, []).append(eval_result)

    attempt_num = len(state["guesses"][player_id])
    log_entries = []

    if word == target:
        state["solved"][player_id] = True
        state["winner"] = [p_name]
        log_entries.append(f"🎉 {p_name} guessed '{word}' in {attempt_num} attempts and WINS!")
    else:
        greens = sum(1 for _, st in eval_result if st == "green")
        yellows = sum(1 for _, st in eval_result if st == "yellow")
        log_entries.append(f"💡 {p_name} submitted '{word}' (Attempt {attempt_num}/{MAX_ATTEMPTS}: {greens} exact, {yellows} close).")

    # Check if both players used all attempts
    p0 = state["players"][0]["id"]
    p1 = state["players"][1]["id"]
    p0_done = state["solved"].get(p0, False) or len(state["guesses"].get(p0, [])) >= MAX_ATTEMPTS
    p1_done = state["solved"].get(p1, False) or len(state["guesses"].get(p1, [])) >= MAX_ATTEMPTS

    if p0_done and p1_done and state["winner"] is None:
        # Both ran out without solving
        state["winner"] = []  # Draw
        log_entries.append(f"💀 Both players ran out of attempts! The secret word was '{target}'.")

    state["turn_index"] += 1
    state["log"].extend(log_entries)
    if len(state["log"]) > 8:
        state["log"] = state["log"][-8:]

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or (
        all(state["solved"].get(p["id"], False) or len(state["guesses"].get(p["id"], [])) >= MAX_ATTEMPTS for p in state["players"])
    )


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def _render_wordle_tile(letter, status):
    if status == "green":
        return paint(f" {letter} ", "1;30;42")  # Black on Green
    elif status == "yellow":
        return paint(f" {letter} ", "1;30;43")  # Black on Yellow
    elif status == "gray":
        return paint(f" {letter} ", "1;37;40")  # Dim Gray
    return paint(" · ", "2")


def _get_keyboard_status(my_guesses):
    """Map each letter A-Z to best known color status."""
    kb = {}
    for g in my_guesses:
        for letter, st in g:
            curr = kb.get(letter)
            if st == "green":
                kb[letter] = "green"
            elif st == "yellow" and curr != "green":
                kb[letter] = "yellow"
            elif st == "gray" and curr not in ("green", "yellow"):
                kb[letter] = "gray"
    return kb


def render_dashboard(view):
    name = view.get("name", "Player")
    opp_name = view.get("opponent_name", "Opponent")
    my_guesses = view.get("my_guesses", [])
    opp_guesses = view.get("opp_guesses", [])
    turn_id = view.get("turn_id")
    my_id = view.get("player_id")
    log = view.get("log", [])

    out = [
        paint("=" * 64, "1;36"),
        paint("                 W O R D L E   V E R S U S", "1;36"),
        paint("=" * 64, "1;36"),
        "",
        f"  {paint(name.upper(), '1;33'):<30}      {paint(opp_name.upper() + ' (Progress)', '1;36')}",
        "  " + "─" * 28 + "      " + "─" * 28
    ]

    # Render 6 rows side by side
    for row in range(MAX_ATTEMPTS):
        # My row
        if row < len(my_guesses):
            my_cells = "".join(_render_wordle_tile(l, st) for l, st in my_guesses[row])
        else:
            my_cells = "".join(_render_wordle_tile("·", "empty") for _ in range(5))

        # Opponent row
        if row < len(opp_guesses):
            opp_cells = "".join(_render_wordle_tile(l, st) for l, st in opp_guesses[row])
        else:
            opp_cells = "".join(_render_wordle_tile("·", "empty") for _ in range(5))

        out.append(f"   Row {row + 1}: {my_cells}             Row {row + 1}: {opp_cells}")

    out.append("")
    out.append("  Legend: " + paint(" GREEN ", "1;30;42") + " Correct spot  |  " +
               paint(" YELLOW ", "1;30;43") + " Wrong spot  |  " +
               paint(" GRAY ", "1;37;40") + " Not in word")
    out.append("")

    # Keyboard Tracker
    kb = _get_keyboard_status(my_guesses)
    kb_lines = [
        "Q W E R T Y U I O P",
        " A S D F G H J K L ",
        "   Z X C V B N M   "
    ]
    out.append("  KEYBOARD TRACKER:")
    for row in kb_lines:
        row_str = "    "
        for char in row.split():
            st = kb.get(char)
            if st == "green":
                styled = paint(char, "1;32")
            elif st == "yellow":
                styled = paint(char, "1;33")
            elif st == "gray":
                styled = paint(char, "2")
            else:
                styled = char
            row_str += styled + " "
        out.append(row_str)

    if log:
        out.append("")
        out.append("  Recent Activity:")
        out.extend("   " + line for line in log[-3:])

    return "\n".join(out)


def render_final(view, message, winners):
    parts = [render_dashboard(view), ""]
    if winners:
        parts.append(paint(f"  🏆  WINNER: {', '.join(winners)}!  🏆", "1;32"))
    else:
        parts.append(paint("  Game ended in a Draw!", "1;33"))
    return "\n".join(parts)
