"""
Bingo 1-25 Game Module.
Supports LAN Multiplayer, Solo vs PC, and Local Pass-and-Play.
"""
import random
import time
from config import paint, clear_screen, USE_COLOR

NUMBERS = list(range(1, 26))
BINGO = "BINGO"

game_id = "bingo"
game_name = "Bingo"
min_players = 2
max_players = 4


def make_lines():
    result = []
    for r in range(5):
        result.append((f"Row {r + 1}", [(r, c) for c in range(5)]))
    for c in range(5):
        result.append((f"Column {c + 1}", [(r, c) for r in range(5)]))
    result.append(("Main diagonal", [(i, i) for i in range(5)]))
    result.append(("Other diagonal", [(i, 4 - i) for i in range(5)]))
    return result


LINES = make_lines()


def hot_numbers(board, called):
    called = set(called)
    hot = set()
    for _, cells in LINES:
        missing = [board[r][c] for r, c in cells if board[r][c] not in called]
        if len(missing) == 1:
            hot.add(missing[0])
    return hot


def letters_text(letters):
    letters = "".join(letters)
    return " ".join(
        paint(ch, "1;32") if i < len(letters) else paint("-", "2")
        for i, ch in enumerate(BINGO)
    )


def render_board(board, called, hot=None):
    called = set(called)
    hot = hot_numbers(board, called) if hot is None else hot
    border = "   +" + "----+" * 5
    lines = ["    " + "".join(f"{'C' + str(c):^4} " for c in range(1, 6)), border]
    for r, row in enumerate(board, 1):
        cells = []
        for n in row:
            if n in called:
                cells.append(paint("  X ", "1;32"))
            elif n in hot:
                cells.append(paint(f" {n:>2}*", "1;33"))
            else:
                cells.append(f" {n:>2} ")
        lines.append(f"R{r} |" + "|".join(cells) + "|")
        lines.append(border)
    return "\n".join(lines)


def render_scores(scores, you_id=None, turn_id=None):
    rows = ["", "  " + "-" * 13 + " SCOREBOARD " + "-" * 13]
    for s in scores:
        pointer = paint("▶", "1;36") if s.get("id") == turn_id else " "
        label = s["name"] + (" (you)" if s.get("id") == you_id else "")
        left = paint("  [left]", "31") if not s.get("online", True) else ""
        rows.append(f"  {pointer} {label:<24} {letters_text(s['letters'])}  {s['score']}/5{left}")
    return "\n".join(rows)


# --- Game Engine Interface ---

def create_board():
    values = NUMBERS[:]
    random.shuffle(values)
    return [values[i:i + 5] for i in range(0, 25, 5)]


def create_state(player_sessions):
    players = []
    for s in player_sessions:
        if isinstance(s, dict):
            pid, name = s["id"], s["name"]
        else:
            pid, name = s.player_id, s.name
        players.append({
            "id": pid,
            "name": name,
            "board": create_board(),
            "completed": set(),
            "letters": []
        })

    return {
        "players": players,
        "called": set(),
        "history": [],
        "turn_index": 0,
        "last_call": None,
        "winner": None
    }


def current_player(state):
    players = state["players"]
    idx = state["turn_index"] % len(players)
    return players[idx]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    scores = [{
        "id": p["id"],
        "name": p["name"],
        "letters": "".join(p["letters"]),
        "score": len(p["letters"]),
        "online": p.get("online", True)
    } for p in state["players"]]

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Guest",
        "board": p_data["board"] if p_data else [],
        "called": sorted(state["called"]),
        "scores": scores,
        "turn_id": current_player(state),
        "last_call": state["last_call"],
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Call a number (1–25)"


def parse_action(state_or_view, player_id, raw_input):
    try:
        val = int(str(raw_input).strip())
    except (ValueError, TypeError):
        return False, "Enter a valid integer from 1 to 25."

    if not 1 <= val <= 25:
        return False, "Number must be between 1 and 25."

    called = state_or_view.get("called", set())
    if isinstance(called, list):
        called = set(called)

    if val in called:
        return False, f"Number {val} was already called."

    return True, val


def apply_action(state, player_id, number):
    state["called"].add(number)
    state["history"].append(number)
    caller_p = next(p for p in state["players"] if p["id"] == player_id)
    state["last_call"] = f"{number} (by {caller_p['name']})"

    log_entries = [f"{caller_p['name']} called {number}"]
    awards = []

    for p in state["players"]:
        board = p["board"]
        now_completed = {
            i for i, (_, cells) in enumerate(LINES)
            if all(board[r][c] in state["called"] for r, c in cells)
        }
        new_lines = sorted(now_completed - p["completed"])
        p["completed"].update(new_lines)

        for line_id in new_lines:
            if len(p["letters"]) < 5:
                letter = BINGO[len(p["letters"])]
                p["letters"].append(letter)
                line_name = LINES[line_id][0]
                awards.append((p["name"], letter, line_name))
                log_entries.append(f"★ {p['name']} completed {line_name} → {letter}")

    # Check for winner(s)
    winners = [p["name"] for p in state["players"] if len(p["letters"]) >= 5]
    if winners:
        state["winner"] = winners

    state["turn_index"] += 1
    return {"log": log_entries, "awards": awards, "number": number}


def is_over(state):
    return state["winner"] is not None or len(state["called"]) >= 25


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    if len(state["called"]) >= 25:
        # Highest score
        max_s = max(len(p["letters"]) for p in state["players"])
        return [p["name"] for p in state["players"] if len(p["letters"]) == max_s]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    name = view.get("name", "Player")
    board = view.get("board", [])
    called = set(view.get("called", []))
    scores = view.get("scores", [])
    you_id = view.get("player_id")
    turn_id = view.get("turn_id")
    last = view.get("last_call")
    log = view.get("log", [])

    my_letters = ""
    for s in scores:
        if s.get("id") == you_id:
            my_letters = s["letters"]

    out = [
        paint("=" * 48, "1;36"),
        paint(f"   B I N G O   1–25   —   {name}", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        render_board(board, called),
        f"  Your letters: {letters_text(my_letters)}",
        "  " + paint("X", "1;32") + " = called    " + paint("n*", "1;33") + " = completes a line if called",
        "",
        "  Still available: " + (" ".join(str(n) for n in NUMBERS if n not in called) or "none"),
    ]
    if last:
        out.append("  Last call: " + paint(last, "1;35"))
    out.append(render_scores(scores, you_id, turn_id))
    if log:
        out.append("")
        out.append("  Recent activity:")
        out.extend("   " + line for line in log)
    return "\n".join(out)


def render_final(view, message, winners):
    name = view.get("name", "Player")
    board = view.get("board", [])
    called = set(view.get("called", []))
    scores = view.get("scores", [])
    you_id = view.get("player_id")

    parts = [render_dashboard(view), ""]
    if winners and name in winners:
        if len(winners) == 1:
            parts.append(paint("  🏆  YOU WIN BINGO!  🏆", "1;32"))
        else:
            others = ", ".join(w for w in winners if w != name)
            parts.append(paint(f"  🏆  It's a tie — you share the win with {others}!  🏆", "1;32"))
    elif winners:
        parts.append(paint(f"  🏆  {message}  🏆", "1;33"))
    else:
        parts.append(paint(f"  {message}", "1;33"))
    return "\n".join(parts)


# --- Standalone Solo vs PC and Local Pass & Play ---

class LocalPlayer:
    def __init__(self, name, human=True):
        self.name = name
        self.human = human
        self.board = create_board()
        self.completed = set()
        self.letters = []

    def update_lines(self, called):
        now = {
            i for i, (_, cells) in enumerate(LINES)
            if all(self.board[r][c] in called for r, c in cells)
        }
        new_ids = sorted(now - self.completed)
        self.completed.update(new_ids)
        awards = []
        for line_id in new_ids:
            if len(self.letters) < 5:
                letter = BINGO[len(self.letters)]
                self.letters.append(letter)
                awards.append((letter, LINES[line_id][0]))
        return awards


def pc_pick(pc, players, called):
    best, best_score = None, float("-inf")
    for number in NUMBERS:
        if number in called:
            continue
        score = random.random() * 0.25
        for _, cells in LINES:
            vals = [pc.board[r][c] for r, c in cells]
            missing = sum(v not in called for v in vals)
            if missing and number in vals:
                score += 8 / missing
                if missing == 1:
                    score += 8
        for other in players:
            if other is pc or not other.human:
                continue
            for _, cells in LINES:
                vals = [other.board[r][c] for r, c in cells]
                if number in vals and sum(v not in called for v in vals) == 1:
                    score -= 2
        if score > best_score:
            best, best_score = number, score
    return best


def run_local_game(players):
    called, history, turn = set(), [], 0
    humans = sum(p.human for p in players)
    while len(called) < 25:
        index = turn % len(players)
        current = players[index]
        clear_screen()
        print(paint(f"\n--- {current.name}'s turn ---", "1;36"))
        if current.human:
            scores = [{"id": i, "name": p.name, "letters": "".join(p.letters), "score": len(p.letters)} for i, p in enumerate(players)]
            v = {
                "name": current.name,
                "board": current.board,
                "called": sorted(called),
                "scores": scores,
                "player_id": index,
                "turn_id": index
            }
            print(render_dashboard(v))
            while True:
                raw = input("\nCall a number (1-25) or Q to quit: ").strip()
                if raw.lower() in {"q", "quit"}:
                    return
                valid, res = parse_action({"called": called}, index, raw)
                if valid:
                    number = res
                    break
                print(paint(f"  ! {res}", "1;31"))
        else:
            number = pc_pick(current, players, called)
            print(f"{current.name} is thinking...", flush=True)
            time.sleep(0.6)
            print(paint(f"{current.name} calls {number}!", "1;35"))

        called.add(number)
        history.append((current.name, number))

        for p in players:
            p.update_lines(called)

        winners = [p for p in players if len(p.letters) >= 5]
        if winners:
            print(paint("\n🏆 " + " AND ".join(p.name for p in winners) + " WINS BINGO! 🏆", "1;32"))
            break

        nxt = players[(turn + 1) % len(players)]
        if humans > 1 and nxt.human:
            input(f"\nPass keyboard to {nxt.name} and press Enter...")
        else:
            input("\nPress Enter for next turn...")
        turn += 1


def solo_setup():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("          BINGO — SOLO VS PC", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = input("Enter your name [You]: ").strip() or "You"
    players = [LocalPlayer(name, human=True)]

    while True:
        try:
            cnt = int(input("How many PC opponents? (1–3): ").strip())
            if 1 <= cnt <= 3:
                break
        except ValueError:
            pass
        print("Please enter 1, 2, or 3.")

    for pc_name in ["PC Nova", "PC Pixel", "PC Turbo"][:cnt]:
        players.append(LocalPlayer(pc_name, human=False))

    input("\nBoards ready! Press Enter to start...")
    run_local_game(players)
