"""
Mastermind Codebreaker Game Module.
2-Player Deductive Logic Game.
"""
from config import paint

game_id = "mastermind"
game_name = "Mastermind"
min_players = 2
max_players = 2


def create_state(player_sessions):
    players = []
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})

    return {
        "players": players,
        "codemaker_id": players[0]["id"],
        "codebreaker_id": players[1]["id"],
        "secret_code": None,  # list of 4 ints e.g. [1, 4, 2, 6]
        "guesses": [],        # list of {"guess": [1,2,3,4], "b": 1, "w": 2}
        "attempts": 0,
        "winner": None
    }


def current_player(state):
    if state["secret_code"] is None:
        return state["codemaker_id"]
    return state["codebreaker_id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    is_codemaker = (player_id == state["codemaker_id"])

    # PRIVACY ENFORCEMENT: Send secret_code ONLY if is_codemaker or game is over
    code_visible = is_codemaker or state["winner"] is not None

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "codemaker_id": state["codemaker_id"],
        "codebreaker_id": state["codebreaker_id"],
        "secret_code": state["secret_code"] if code_visible else None,
        "guesses": state["guesses"],
        "attempts": state["attempts"],
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    if state_or_view.get("secret_code") is None and player_id == state_or_view.get("codemaker_id"):
        return "Set secret 4-digit code using numbers 1–6 (e.g. '1 4 2 6')"
    return "Enter 4-digit guess using numbers 1–6 (e.g. '1 2 3 4')"


def parse_action(state_or_view, player_id, raw_input):
    parts = str(raw_input).strip().split()
    if len(parts) != 4:
        return False, "Enter exactly 4 digits between 1 and 6 separated by spaces (e.g. '1 4 2 6')."

    try:
        digits = [int(p) for p in parts]
    except ValueError:
        return False, "All 4 entries must be numbers."

    if any(d < 1 or d > 6 for d in digits):
        return False, "Each digit must be between 1 and 6."

    return True, digits


def calculate_pegs(secret, guess):
    b = 0
    s_unmatched = []
    g_unmatched = []

    for i in range(4):
        if guess[i] == secret[i]:
            b += 1
        else:
            s_unmatched.append(secret[i])
            g_unmatched.append(guess[i])

    w = 0
    for g in g_unmatched:
        if g in s_unmatched:
            w += 1
            s_unmatched.remove(g)

    return b, w


def apply_action(state, player_id, digits):
    log_entries = []
    cm_name = next(p["name"] for p in state["players"] if p["id"] == state["codemaker_id"])
    cb_name = next(p["name"] for p in state["players"] if p["id"] == state["codebreaker_id"])

    if state["secret_code"] is None:
        state["secret_code"] = digits
        log_entries.append(f"🔐 {cm_name} has secretly set the 4-digit code! {cb_name}'s turn to guess.")
        return {"log": log_entries}

    # Codebreaker turn
    state["attempts"] += 1
    b, w = calculate_pegs(state["secret_code"], digits)
    state["guesses"].append({"guess": digits, "b": b, "w": w})

    guess_str = " ".join(str(d) for d in digits)
    log_entries.append(f"Attempt {state['attempts']}/10: {cb_name} guessed [{guess_str}] → Feedback: {b} Black Peg(s), {w} White Peg(s)")

    if b == 4:
        state["winner"] = [cb_name]
        log_entries.append(f"🎉 {cb_name} CRACKED THE CODE [{guess_str}] in {state['attempts']} attempts and WINS!")
    elif state["attempts"] >= 10:
        state["winner"] = [cm_name]
        sec_str = " ".join(str(d) for d in state["secret_code"])
        log_entries.append(f"💀 {cb_name} ran out of attempts! {cm_name} WINS! Secret code was [{sec_str}].")

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or state["attempts"] >= 10


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    pass


def render_dashboard(view):
    attempts = view.get("attempts", 0)
    guesses = view.get("guesses", [])
    sec_code = view.get("secret_code")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("             M A S T E R M I N D", "1;36"),
        paint("=" * 48, "1;36"),
        ""
    ]

    if sec_code:
        out.append("  Secret Code: " + paint(" ".join(f"[{d}]" for d in sec_code), "1;32"))
    else:
        out.append("  Secret Code: " + paint("[ ?  ?  ?  ? ]", "2"))

    out.append(f"  Attempts: {attempts}/10")
    out.append("")
    out.append("  GUESS HISTORY:")

    if not guesses:
        out.append("   (No guesses yet)")
    else:
        for idx, g in enumerate(guesses, 1):
            g_str = " ".join(f"[{d}]" for d in g["guess"])
            feedback = paint(f"{g['b']} Black, {g['w']} White", "1;33")
            out.append(f"   {idx:>2}. {g_str}  →  {feedback}")

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
