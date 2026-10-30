"""
Liar's Dice Game Module.
2–4 Player Bluffing & Hidden Information Game.
"""
import random
from config import paint

game_id = "liars_dice"
game_name = "Liar's Dice"
min_players = 2
max_players = 4


def roll_dice(count):
    return sorted([random.randint(1, 6) for _ in range(count)])


def create_state(player_sessions):
    players = []
    dice = {}
    remaining_dice = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        dice[pid] = roll_dice(5)
        remaining_dice[pid] = 5

    return {
        "players": players,
        "dice": dice,
        "remaining_dice": remaining_dice,
        "turn_index": 0,
        "current_bid": None,  # tuple (pid, quantity, face)
        "round": 1,
        "winner": None,
        "last_challenge_result": None
    }


def active_players(state):
    return [p for p in state["players"] if state["remaining_dice"][p["id"]] > 0]


def current_player(state):
    actives = active_players(state)
    if not actives:
        return state["players"][0]["id"]
    return actives[state["turn_index"] % len(actives)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)

    # PRIVACY ENFORCEMENT: Send ONLY own dice!
    own_dice = state["dice"].get(player_id, []) if state["remaining_dice"].get(player_id, 0) > 0 else []

    remaining_summary = [
        {
            "id": p["id"],
            "name": p["name"],
            "dice_count": state["remaining_dice"][p["id"]]
        }
        for p in state["players"]
    ]

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "own_dice": own_dice,
        "remaining_summary": remaining_summary,
        "current_bid": state["current_bid"],
        "round": state["round"],
        "turn_id": current_player(state),
        "winner": state["winner"],
        "last_challenge_result": state["last_challenge_result"]
    }


def prompt_for(state_or_view, player_id):
    bid = state_or_view.get("current_bid")
    if not bid:
        return "Enter initial bid (e.g. '3 4' for three 4s)"
    return "Enter higher bid (e.g. '4 4') or 'C' / 'challenge'"


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip().lower()
    current_bid = state_or_view.get("current_bid")

    if text in {"c", "challenge", "liar"}:
        if not current_bid:
            return False, "Cannot challenge when there is no active bid!"
        return True, {"type": "challenge"}

    parts = text.split()
    if len(parts) != 2:
        return False, "Format: '<quantity> <face>' (e.g. '3 4') or 'C' to challenge."

    try:
        qty = int(parts[0])
        face = int(parts[1])
    except ValueError:
        return False, "Quantity and face must be whole numbers."

    if qty < 1:
        return False, "Quantity must be at least 1."
    if not 1 <= face <= 6:
        return False, "Face value must be between 1 and 6."

    if current_bid:
        _, curr_qty, curr_face = current_bid
        if qty < curr_qty:
            return False, f"Bid quantity must be >= {curr_qty}."
        if qty == curr_qty and face <= curr_face:
            return False, f"At quantity {qty}, face value must be > {curr_face}."

    return True, {"type": "bid", "qty": qty, "face": face}


def apply_action(state, player_id, action):
    actives = active_players(state)
    curr_player = next(p for p in state["players"] if p["id"] == player_id)
    log_entries = []

    if action["type"] == "bid":
        qty = action["qty"]
        face = action["face"]
        state["current_bid"] = (player_id, qty, face)
        log_entries.append(f"{curr_player['name']} bid {qty} × [{face}]s")
        state["turn_index"] += 1
        return {"log": log_entries}

    elif action["type"] == "challenge":
        bidder_id, qty, face = state["current_bid"]
        bidder = next(p for p in state["players"] if p["id"] == bidder_id)

        # Count total matching dice across ALL players
        total_matching = 0
        all_revealed = {}
        for p in actives:
            pid = p["id"]
            p_dice = state["dice"][pid]
            all_revealed[p["name"]] = list(p_dice)
            total_matching += sum(1 for d in p_dice if d == face)

        log_entries.append(f"🔥 {curr_player['name']} challenged {bidder['name']}'s bid of {qty} × [{face}]s!")
        log_entries.append(f"Revealed dice count for [{face}]s: {total_matching}")

        if total_matching >= qty:
            # Bid was truthful! Challenger loses a die
            loser = curr_player
            log_entries.append(f"Result: Bid was VALID! {curr_player['name']} loses 1 die.")
        else:
            # Bluff caught! Bidder loses a die
            loser = bidder
            log_entries.append(f"Result: BLUFF CAUGHT! {bidder['name']} loses 1 die.")

        state["remaining_dice"][loser["id"]] -= 1
        if state["remaining_dice"][loser["id"]] == 0:
            log_entries.append(f"💀 {loser['name']} has lost all dice and is ELIMINATED!")

        # Check for winner
        survivors = active_players(state)
        if len(survivors) == 1:
            state["winner"] = [survivors[0]["name"]]
            log_entries.append(f"🏆 {survivors[0]['name']} is the last surviving player and wins!")
        else:
            # Next round: reroll dice for survivors
            state["round"] += 1
            state["current_bid"] = None
            for p in survivors:
                state["dice"][p["id"]] = roll_dice(state["remaining_dice"][p["id"]])
            state["turn_index"] = 0

        state["last_challenge_result"] = {
            "challenger": curr_player["name"],
            "bidder": bidder["name"],
            "bid": (qty, face),
            "actual": total_matching,
            "loser": loser["name"],
            "all_revealed": all_revealed
        }

        return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None or len(active_players(state)) <= 1


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    survivors = active_players(state)
    if len(survivors) == 1:
        return [survivors[0]["name"]]
    return []


def skip_player(state, player_id):
    actives = active_players(state)
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    name = view.get("name", "Player")
    own_dice = view.get("own_dice", [])
    summary = view.get("remaining_summary", [])
    current_bid = view.get("current_bid")
    turn_id = view.get("turn_id")
    rnd = view.get("round", 1)
    log = view.get("log", [])
    last_challenge = view.get("last_challenge_result")

    out = [
        paint("=" * 48, "1;36"),
        paint(f"        L I A R ' S   D I C E   (Round {rnd})", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        f"  Player: {name}"
    ]

    if own_dice:
        dice_str = " ".join(paint(f"[{d}]", "1;33") for d in own_dice)
        out.append(f"  Your secret dice: {dice_str}")
    else:
        out.append(paint("  Your dice: (Eliminated)", "31"))

    out.append("")
    out.append("  PLAYERS REMAINING:")
    for p in summary:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        status = f"{p['dice_count']} dice" if p["dice_count"] > 0 else paint("ELIMINATED", "31")
        out.append(f"   {ptr} {p['name']:<20} {status}")

    out.append("")
    if current_bid:
        b_id, qty, face = current_bid
        b_name = next((p["name"] for p in summary if p["id"] == b_id), "Someone")
        out.append(f"  Current Bid: " + paint(f"{qty} × [{face}]s", "1;35") + f" by {b_name}")
    else:
        out.append("  Current Bid: " + paint("None (Bidding starts)", "2"))

    if last_challenge:
        out.append("")
        out.append(paint("  LAST CHALLENGE DETAILS:", "1;32"))
        out.append(f"   {last_challenge['challenger']} challenged {last_challenge['bidder']}'s bid of {last_challenge['bid'][0]}×[{last_challenge['bid'][1]}]s")
        out.append(f"   Actual count was {last_challenge['actual']} → {last_challenge['loser']} lost 1 die.")
        if "all_revealed" in last_challenge:
            for p_name, p_dice in last_challenge["all_revealed"].items():
                out.append(f"     {p_name}: {' '.join(f'[{d}]' for d in p_dice)}")

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
