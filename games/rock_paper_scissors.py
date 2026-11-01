"""
Rock, Paper, Scissors (Best of 3) Game Module.
2-Player Simultaneous Choice Strategy Game.
"""
from config import paint

game_id = "rock_paper_scissors"
game_name = "Rock, Paper, Scissors"
min_players = 2
max_players = 2

TARGET_WINS = 2
CHOICES = {"R": "Rock", "P": "Paper", "S": "Scissors"}


def create_state(player_sessions):
    players = []
    scores = {}
    moves = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        scores[pid] = 0

    return {
        "players": players,
        "scores": scores,
        "moves": moves,  # pid -> "R", "P", "S"
        "round": 1,
        "winner": None,
        "last_result": None
    }


def current_player(state):
    # Whoever hasn't submitted a move for the current round
    for p in state["players"]:
        if p["id"] not in state["moves"]:
            return p["id"]
    return state["players"][0]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    opp = next((p for p in state["players"] if p["id"] != player_id), None)

    my_move = state["moves"].get(player_id)
    opp_moved = opp["id"] in state["moves"] if opp else False

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "opponent_name": opp["name"] if opp else "Opponent",
        "players": state["players"],
        "scores": state["scores"],
        "my_move": my_move,
        "opp_moved": opp_moved,
        "round": state["round"],
        "turn_id": current_player(state),
        "winner": state["winner"],
        "last_result": state["last_result"]
    }


def prompt_for(state_or_view, player_id):
    return "Choose: 'R' (Rock), 'P' (Paper), or 'S' (Scissors)"


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip().upper()
    if text in {"R", "ROCK"}:
        return True, "R"
    if text in {"P", "PAPER"}:
        return True, "P"
    if text in {"S", "SCISSORS"}:
        return True, "S"

    return False, "Invalid move! Enter 'R' for Rock, 'P' for Paper, or 'S' for Scissors."


def apply_action(state, player_id, move):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    state["moves"][player_id] = move
    log_entries = [f"{curr_p['name']} locked in their choice for Round {state['round']}."]

    # Check if both players submitted moves
    if len(state["moves"]) == 2:
        p1, p2 = state["players"][0], state["players"][1]
        m1, m2 = state["moves"][p1["id"]], state["moves"][p2["id"]]

        choice1, choice2 = CHOICES[m1], CHOICES[m2]
        log_entries.append(f"⚔️ Round {state['round']} REVEAL: {p1['name']} [{choice1}] vs {p2['name']} [{choice2}]")

        if m1 == m2:
            log_entries.append("🤝 Round result: IT'S A TIE!")
        elif (m1 == "R" and m2 == "S") or (m1 == "S" and m2 == "P") or (m1 == "P" and m2 == "R"):
            state["scores"][p1["id"]] += 1
            log_entries.append(f"🔥 {p1['name']} wins Round {state['round']}! ({choice1} beats {choice2})")
        else:
            state["scores"][p2["id"]] += 1
            log_entries.append(f"🔥 {p2['name']} wins Round {state['round']}! ({choice2} beats {choice1})")

        # Check match winner
        if state["scores"][p1["id"]] >= TARGET_WINS:
            state["winner"] = [p1["name"]]
            log_entries.append(f"🏆 {p1['name']} reaches {TARGET_WINS} wins and WINS THE MATCH!")
        elif state["scores"][p2["id"]] >= TARGET_WINS:
            state["winner"] = [p2["name"]]
            log_entries.append(f"🏆 {p2['name']} reaches {TARGET_WINS} wins and WINS THE MATCH!")
        else:
            state["round"] += 1
            state["moves"] = {}  # Reset for next round

    return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    pass


def render_dashboard(view):
    players = view.get("players", [])
    scores = view.get("scores", {})
    rnd = view.get("round", 1)
    my_move = view.get("my_move")
    opp_moved = view.get("opp_moved", False)
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint(f"   R O C K   P A P E R   S C I S S O R S   (R{rnd})", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        f"  First to {TARGET_WINS} wins wins the match!",
        ""
    ]

    for p in players:
        sc = scores.get(p["id"], 0)
        out.append(f"  {p['name']:<20} Score: {sc}/{TARGET_WINS}")

    out.append("")
    if my_move:
        out.append("  Your move: " + paint(f"[{CHOICES.get(my_move)}]", "1;32") + " (Locked in)")
    else:
        out.append("  Your move: " + paint("[ Waiting for your choice... ]", "2"))

    if opp_moved:
        out.append("  Opponent: " + paint("[ Choice Locked In ]", "1;33"))
    else:
        out.append("  Opponent: " + paint("[ Thinking... ]", "2"))

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
