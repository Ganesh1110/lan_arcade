"""
Hangman Game Module.
2-Player Word Guessing Game.
"""
from config import paint

game_id = "hangman"
game_name = "Hangman"
min_players = 2
max_players = 2

MAX_WRONG = 6

STAGES = [
    """
       +---+
       |   |
           |
           |
           |
           |
     =========
    """,
    """
       +---+
       |   |
       O   |
           |
           |
           |
     =========
    """,
    """
       +---+
       |   |
       O   |
       |   |
           |
           |
     =========
    """,
    """
       +---+
       |   |
       O   |
      /|   |
           |
           |
     =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
           |
           |
     =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
      /    |
           |
     =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
      / \\  |
           |
     =========
    """
]


def create_state(player_sessions):
    players = []
    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})

    return {
        "players": players,
        "wordmaster_id": players[0]["id"],
        "guesser_id": players[1]["id"],
        "secret_word": None,
        "guessed_letters": set(),
        "wrong_count": 0,
        "winner": None
    }


def current_player(state):
    if state["secret_code"] is None if "secret_code" in state else state["secret_word"] is None:
        return state["wordmaster_id"]
    return state["guesser_id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    is_wordmaster = (player_id == state["wordmaster_id"])

    # PRIVACY ENFORCEMENT: Send secret word ONLY to Wordmaster or when game is over
    word_visible = is_wordmaster or state["winner"] is not None

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "wordmaster_id": state["wordmaster_id"],
        "guesser_id": state["guesser_id"],
        "secret_word": state["secret_word"] if word_visible else None,
        "guessed_letters": sorted(list(state["guessed_letters"])),
        "wrong_count": state["wrong_count"],
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    if state_or_view.get("secret_word") is None and player_id == state_or_view.get("wordmaster_id"):
        return "Set secret word/phrase (e.g. 'COMPUTER')"
    return "Enter a single letter guess (e.g. 'A' or 'E')"


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip().upper()
    if not text:
        return False, "Input cannot be empty."

    # Word Master setting secret word
    if state_or_view.get("secret_word") is None and player_id == state_or_view.get("wordmaster_id"):
        clean_word = "".join(ch for ch in text if ch.isalpha())
        if len(clean_word) < 2:
            return False, "Secret word must contain at least 2 letters (A–Z)."
        return True, clean_word

    # Guesser turn
    if len(text) != 1 or not text.isalpha():
        return False, "Guess must be a single letter (A–Z)."

    guessed = set(state_or_view.get("guessed_letters", []))
    if text in guessed:
        return False, f"Letter '{text}' was already guessed! Choose another."

    return True, text


def apply_action(state, player_id, action_val):
    log_entries = []
    wm_name = next(p["name"] for p in state["players"] if p["id"] == state["wordmaster_id"])
    g_name = next(p["name"] for p in state["players"] if p["id"] == state["guesser_id"])

    if state["secret_word"] is None:
        state["secret_word"] = action_val
        log_entries.append(f"🔒 {wm_name} set a secret word ({len(action_val)} letters)! {g_name}'s turn to guess.")
        return {"log": log_entries}

    letter = action_val
    state["guessed_letters"].add(letter)

    if letter in state["secret_word"]:
        log_entries.append(f"✨ {g_name} guessed '{letter}' — GOOD GUESS!")
    else:
        state["wrong_count"] += 1
        log_entries.append(f"❌ {g_name} guessed '{letter}' — NOT in the word! ({state['wrong_count']}/{MAX_WRONG} wrong)")

    # Check win condition (all letters in secret_word revealed)
    word_letters = set(state["secret_word"])
    if word_letters.issubset(state["guessed_letters"]):
        state["winner"] = [g_name]
        log_entries.append(f"🏆 {g_name} guessed the word '{state['secret_word']}' and WINS!")
    elif state["wrong_count"] >= MAX_WRONG:
        state["winner"] = [wm_name]
        log_entries.append(f"💀 {g_name} ran out of guesses! {wm_name} WINS! Word was '{state['secret_word']}'.")

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or state["wrong_count"] >= MAX_WRONG


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    pass


def render_dashboard(view):
    sec_word = view.get("secret_word")
    guessed = set(view.get("guessed_letters", []))
    wrong_cnt = view.get("wrong_count", 0)
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("                 H A N G M A N", "1;36"),
        paint("=" * 48, "1;36"),
        ""
    ]

    # Render Gallows ASCII Art
    stage_idx = min(wrong_cnt, MAX_WRONG)
    out.append(paint(STAGES[stage_idx], "1;33"))

    # Render Word Blanks
    if sec_word:
        display_word = " ".join(ch if ch in guessed else "_" for ch in sec_word)
        out.append("  Word: " + paint(display_word, "1;32"))
    else:
        out.append("  Word: " + paint("_ _ _ _ _", "2"))

    guessed_str = " ".join(sorted(list(guessed))) if guessed else "None"
    out.append(f"  Guessed letters: {guessed_str}")

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
