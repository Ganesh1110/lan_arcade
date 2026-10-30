"""
Dots and Boxes Game Module.
2–4 Player Territorial Strategy Game.
"""
from config import paint

game_id = "dots_and_boxes"
game_name = "Dots and Boxes"
min_players = 2
max_players = 4

DOTS_ROWS = 4
DOTS_COLS = 4


def create_state(player_sessions):
    players = []
    scores = {}
    symbols = {}
    sym_list = ["A", "B", "C", "D"]

    for idx, s in enumerate(player_sessions):
        pid = s["id"] if isinstance(s, dict) else s.player_id
        name = s["name"] if isinstance(s, dict) else s.name
        players.append({"id": pid, "name": name})
        scores[pid] = 0
        symbols[pid] = sym_list[idx % len(sym_list)]

    # H[r][c] for r in 0..3, c in 0..2 (Horizontal edges)
    h_edges = [[False] * 3 for _ in range(4)]
    # V[r][c] for r in 0..2, c in 0..3 (Vertical edges)
    v_edges = [[False] * 4 for _ in range(3)]
    # Boxes[r][c] for r in 0..2, c in 0..2 (Box owner symbol)
    boxes = [[None] * 3 for _ in range(3)]

    return {
        "players": players,
        "scores": scores,
        "symbols": symbols,
        "h_edges": h_edges,
        "v_edges": v_edges,
        "boxes": boxes,
        "turn_index": 0,
        "total_lines": 0,
        "winner": None
    }


def current_player(state):
    players = state["players"]
    return players[state["turn_index"] % len(players)]["id"]


def view_for(state, player_id):
    p_data = next((p for p in state["players"] if p["id"] == player_id), None)
    return {
        "player_id": player_id,
        "name": p_data["name"] if p_data else "Player",
        "players": state["players"],
        "scores": state["scores"],
        "symbols": state["symbols"],
        "h_edges": state["h_edges"],
        "v_edges": state["v_edges"],
        "boxes": state["boxes"],
        "turn_id": current_player(state),
        "winner": state["winner"]
    }


def prompt_for(state_or_view, player_id):
    return "Enter edge (e.g. 'H 1 1' or 'V 2 3')"


def parse_action(state_or_view, player_id, raw_input):
    parts = str(raw_input).strip().upper().split()
    if len(parts) != 3:
        return False, "Format: 'H <row> <col>' or 'V <row> <col>' (e.g. 'H 1 1')."

    kind, r_str, c_str = parts[0], parts[1], parts[2]
    if kind not in {"H", "V"}:
        return False, "Edge type must be 'H' (horizontal) or 'V' (vertical)."

    try:
        r = int(r_str) - 1
        c = int(c_str) - 1
    except ValueError:
        return False, "Row and Column must be whole numbers."

    h_edges = state_or_view["h_edges"]
    v_edges = state_or_view["v_edges"]

    if kind == "H":
        if not (0 <= r < 4 and 0 <= c < 3):
            return False, "Horizontal edge row must be 1–4, col 1–3."
        if h_edges[r][c]:
            return False, f"Horizontal edge H {r + 1} {c + 1} is already drawn!"
    else:
        if not (0 <= r < 3 and 0 <= c < 4):
            return False, "Vertical edge row must be 1–3, col 1–4."
        if v_edges[r][c]:
            return False, f"Vertical edge V {r + 1} {c + 1} is already drawn!"

    return True, {"kind": kind, "r": r, "c": c}


def apply_action(state, player_id, edge):
    kind, r, c = edge["kind"], edge["r"], edge["c"]
    curr_p = next(p for p in state["players"] if p["id"] == player_id)
    sym = state["symbols"][player_id]

    if kind == "H":
        state["h_edges"][r][c] = True
    else:
        state["v_edges"][r][c] = True

    state["total_lines"] += 1
    log_msg = f"{curr_p['name']} placed {kind} {r + 1} {c + 1}"

    # Check box completion
    boxes_claimed = 0
    h_edges = state["h_edges"]
    v_edges = state["v_edges"]
    boxes = state["boxes"]

    for br in range(3):
        for bc in range(3):
            if boxes[br][bc] is None:
                top = h_edges[br][bc]
                bottom = h_edges[br + 1][bc]
                left = v_edges[br][bc]
                right = v_edges[br][bc + 1]

                if top and bottom and left and right:
                    boxes[br][bc] = sym
                    boxes_claimed += 1

    if boxes_claimed > 0:
        state["scores"][player_id] += boxes_claimed
        log_msg += f" and completed {boxes_claimed} box(es)! (Gets extra turn)"
    else:
        state["turn_index"] += 1

    # Check Game Over (all 24 lines placed)
    if state["total_lines"] >= 24:
        max_score = max(state["scores"].values())
        state["winner"] = [p["name"] for p in state["players"] if state["scores"][p["id"]] == max_score]
        log_msg += " All lines placed! Game Over."

    return {"log": [log_msg]}


def is_over(state):
    return state["winner"] is not None or state["total_lines"] >= 24


def get_winner(state):
    if state["winner"]:
        return state["winner"]
    return []


def skip_player(state, player_id):
    if current_player(state) == player_id:
        state["turn_index"] += 1


def render_dashboard(view):
    players = view.get("players", [])
    scores = view.get("scores", {})
    symbols = view.get("symbols", {})
    h = view.get("h_edges", [[False] * 3 for _ in range(4)])
    v = view.get("v_edges", [[False] * 4 for _ in range(3)])
    boxes = view.get("boxes", [[None] * 3 for _ in range(3)])
    turn_id = view.get("turn_id")
    log = view.get("log", [])

    out = [
        paint("=" * 48, "1;36"),
        paint("         D O T S   A N D   B O X E S", "1;36"),
        paint("=" * 48, "1;36"),
        ""
    ]

    # Render Board
    board_lines = []
    for r in range(3):
        # Dot row + horizontal edges
        row_str = ["  •"]
        for c in range(3):
            edge = paint("---", "1;33") if h[r][c] else "   "
            row_str.append(edge + "•")
        board_lines.append("".join(row_str) + f"  (H {r + 1})")

        # Vertical edges + boxes
        v_str = ["  "]
        for c in range(3):
            v_edge = paint("|", "1;33") if v[r][c] else " "
            b_sym = paint(f" {boxes[r][c]} ", "1;32") if boxes[r][c] else "   "
            v_str.append(v_edge + b_sym)
        v_edge_last = paint("|", "1;33") if v[r][3] else " "
        v_str.append(v_edge_last)
        board_lines.append("".join(v_str) + f"  (V {r + 1})")

    # Final bottom dot row
    row_str = ["  •"]
    for c in range(3):
        edge = paint("---", "1;33") if h[3][c] else "   "
        row_str.append(edge + "•")
    board_lines.append("".join(row_str) + "  (H 4)")

    out.extend(board_lines)

    out.append("")
    out.append("  SCOREBOARD:")
    for p in players:
        ptr = paint("▶", "1;36") if p["id"] == turn_id else " "
        sym = symbols.get(p["id"], "?")
        score = scores.get(p["id"], 0)
        out.append(f"   {ptr} {p['name']:<20} [{sym}] Score: {score}")

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
        parts.append(paint("  🤝  GAME DRAW!  🤝", "1;33"))
    return "\n".join(parts)
