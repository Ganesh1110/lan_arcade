"""
UNO / Card Craze Game Module.
2–4 Player Card Shedding Game.
"""
import random
from config import paint

game_id = "uno"
game_name = "UNO"
min_players = 2
max_players = 4

COLORS = ["Red", "Green", "Blue", "Yellow"]
COLOR_CODES = {"Red": "1;31", "Green": "1;32", "Blue": "1;34", "Yellow": "1;33"}


def create_deck():
    deck = []
    for color in COLORS:
        deck.append({"color": color, "value": "0"})
        for val in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "+2"]:
            deck.append({"color": color, "value": val})
            deck.append({"color": color, "value": val})

    for _ in range(4):
        deck.append({"color": "Wild", "value": "Wild"})
        deck.append({"color": "Wild", "value": "Wild +4"})

    random.shuffle(deck)
    return deck


def card_str(card):
    color = card["color"]
    val = card["value"]
    if color in COLOR_CODES:
        return paint(f"[{color} {val}]", COLOR_CODES[color])
    return paint(f"[{val}]", "1;35")


def create_state(player_sessions):
    deck = create_deck()
    players = []
    hands = {}

    for s in player_sessions:
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        hands[pid] = [deck.pop() for _ in range(7)]

    # Initial discard top card (must not be Wild)
    top_card = deck.pop()
    while top_card["color"] == "Wild":
        deck.append(top_card)
        random.shuffle(deck)
        top_card = deck.pop()

    return {
        "players": players,
        "hands": hands,
        "deck": deck,
        "discard": [top_card],
        "active_color": top_card["color"],
        "turn_index": 0,
        "direction": 1,  # 1 = clockwise, -1 = counter-clockwise
        "winner": None
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)

    # PRIVACY ENFORCEMENT: Send ONLY own hand
    own_hand = state["hands"].get(player_id, [])

    opponents_summary = [
        {
            "id": p["id"],
            "name": p["name"],
            "card_count": len(state["hands"].get(p["id"], []))
        }
        for p in state["players"]
    ]

    top_card = state["discard"][-1]

    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "own_hand": own_hand,
        "opponents_summary": opponents_summary,
        "top_card": top_card,
        "active_color": state["active_color"],
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter card index to play (1–N), 'D' to draw, or 'W Red/Green/Blue/Yellow' for Wild"


def parse_action(state_or_view, player_id, raw_input):
    text = str(raw_input).strip()
    if not text:
        return False, "Enter a card index (e.g. '1'), 'D' to draw, or '1 Red' for Wild."

    if text.lower() in {"d", "draw"}:
        return True, {"type": "draw"}

    parts = text.split()
    try:
        idx = int(parts[0]) - 1
    except ValueError:
        return False, "Card index must be a number."

    own_hand = state_or_view.get("own_hand", [])
    if not 0 <= idx < len(own_hand):
        return False, f"Invalid card index. Choose between 1 and {len(own_hand)}."

    card = own_hand[idx]
    top_card = state_or_view["top_card"]
    active_color = state_or_view["active_color"]

    # Check Wild color selection
    chosen_color = None
    if card["color"] == "Wild":
        if len(parts) >= 2 and parts[1].capitalize() in COLORS:
            chosen_color = parts[1].capitalize()
        else:
            return False, "Wild card played! Specify color e.g. '1 Red' or '1 Blue'."

    # Check validity
    valid_play = False
    if card["color"] == "Wild":
        valid_play = True
    elif card["color"] == active_color or card["value"] == top_card["value"]:
        valid_play = True

    if not valid_play:
        return False, f"Cannot play {card_str(card)}. Must match color '{active_color}' or value '{top_card['value']}'."

    return True, {"type": "play", "card_index": idx, "chosen_color": chosen_color}


def apply_action(state, player_id, action):
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    hand = state["hands"][player_id]
    log_entries = []

    def refill_deck_if_needed():
        if len(state["deck"]) <= 2:
            top = state["discard"].pop()
            state["deck"].extend(state["discard"])
            state["discard"] = [top]
            random.shuffle(state["deck"])

    if action["type"] == "draw":
        refill_deck_if_needed()
        drawn = state["deck"].pop()
        hand.append(drawn)
        log_entries.append(f"{curr_p['name']} drew a card.")
        state["turn_index"] += state["direction"]
        return {"log": log_entries}

    elif action["type"] == "play":
        idx = action["card_index"]
        card = hand.pop(idx)
        state["discard"].append(card)

        if card["color"] == "Wild":
            state["active_color"] = action["chosen_color"]
            log_entries.append(f"{curr_p['name']} played {card_str(card)} and set color to {action['chosen_color']}!")
        else:
            state["active_color"] = card["color"]
            log_entries.append(f"{curr_p['name']} played {card_str(card)}!")

        # Check win
        if len(hand) == 0:
            state["winner"] = [curr_p["name"]]
            log_entries.append(f"🏆 {curr_p['name']} has no cards left and WINS UNO!")
            return {"log": log_entries}

        if len(hand) == 1:
            log_entries.append(f"🔥 {curr_p['name']} shouts UNO!")

        # Process action effects
        val = card["value"]
        num_players = len(state["players"])

        if val == "Skip":
            log_entries.append("Next player skipped!")
            state["turn_index"] += 2 * state["direction"]
        elif val == "Reverse":
            state["direction"] *= -1
            log_entries.append("Direction reversed!")
            state["turn_index"] += state["direction"]
        elif val == "+2":
            next_idx = (state["turn_index"] + state["direction"]) % num_players
            next_pid = state["players"][next_idx]["id"]
            next_p = state["players"][next_idx]
            refill_deck_if_needed()
            state["hands"][next_pid].extend([state["deck"].pop(), state["deck"].pop()])
            log_entries.append(f"{next_p['name']} drew 2 cards and was skipped!")
            state["turn_index"] += 2 * state["direction"]
        elif val == "Wild +4":
            next_idx = (state["turn_index"] + state["direction"]) % num_players
            next_pid = state["players"][next_idx]["id"]
            next_p = state["players"][next_idx]
            refill_deck_if_needed()
            for _ in range(4):
                refill_deck_if_needed()
                state["hands"][next_pid].append(state["deck"].pop())
            log_entries.append(f"{next_p['name']} drew 4 cards and was skipped!")
            state["turn_index"] += 2 * state["direction"]
        else:
            state["turn_index"] += state["direction"]

        return {"log": log_entries}


def is_over(state):
    return state["winner"] is not None


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += state["direction"]


def render_dashboard(view):
    name = view.get("name", "Player")
    hand = view.get("own_hand", [])
    summary = view.get("opponents_summary", [])
    top_card = view.get("top_card", {"color": "?", "value": "?"})
    active_color = view.get("active_color", "Red")
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("                   U N O", "1;36"),
        paint("=" * 48, "1;36"),
        "",
        f"  Active Color: " + paint(f" {active_color} ", COLOR_CODES.get(active_color, "1;35")) +
        f"   Top Discard: {card_str(top_card)}",
        "",
        "  YOUR HAND:"
    ]

    hand_str = []
    for i, card in enumerate(hand, 1):
        hand_str.append(f"  {i}. {card_str(card)}")
    out.extend(hand_str)

    out.append("")
    out.append("  PLAYERS:")
    for p in summary:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        out.append(f"   {ptr} {p['name']:<20} {p['card_count']} cards")

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
