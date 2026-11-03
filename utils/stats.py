"""
Persistent stats and Hall of Fame tracking for LAN Arcade.
Stores game outcomes, win/loss records, win streaks, and high scores in data/stats.json.
"""
import json
import os
import threading
from config import paint

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_STATS_FILE = os.path.join(_DATA_DIR, "stats.json")
_LOCK = threading.Lock()


def _load_data():
    if not os.path.exists(_STATS_FILE):
        return {
            "players": {},       # name -> {wins, losses, streak, best_streak, games_played}
            "high_scores": {},   # game_id -> [{player, score, detail, date}]
            "recent_matches": [] # [{game, winners, players, timestamp}]
        }
    try:
        with open(_STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"players": {}, "high_scores": {}, "recent_matches": []}


def _save_data(data):
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def record_match_outcome(game_name, player_names, winner_names):
    """Update win/loss records and recent match history."""
    with _LOCK:
        data = _load_data()
        players = data.setdefault("players", {})

        winners_set = set(winner_names)
        is_draw = (len(winner_names) == 0 or len(winner_names) == len(player_names))

        for name in player_names:
            p_stat = players.setdefault(name, {
                "games": 0,
                "wins": 0,
                "losses": 0,
                "streak": 0,
                "best_streak": 0
            })
            p_stat["games"] += 1
            if name in winners_set and not is_draw:
                p_stat["wins"] += 1
                p_stat["streak"] += 1
                if p_stat["streak"] > p_stat["best_streak"]:
                    p_stat["best_streak"] = p_stat["streak"]
            elif not is_draw:
                p_stat["losses"] += 1
                p_stat["streak"] = 0

        # Record recent match
        import time
        date_str = time.strftime("%Y-%m-%d %H:%M")
        matches = data.setdefault("recent_matches", [])
        matches.insert(0, {
            "game": game_name,
            "players": player_names,
            "winners": winner_names,
            "date": date_str
        })
        if len(matches) > 15:
            data["recent_matches"] = matches[:15]

        _save_data(data)


def record_high_score(game_id, player_name, score, detail=None):
    """Record high score for score-based games (2048, Boggle, Anagrams, etc.)."""
    with _LOCK:
        data = _load_data()
        high_scores = data.setdefault("high_scores", {})
        scores_list = high_scores.setdefault(game_id, [])

        import time
        date_str = time.strftime("%Y-%m-%d")

        scores_list.append({
            "player": player_name,
            "score": score,
            "detail": detail or "",
            "date": date_str
        })
        # Sort descending by score, keep top 5
        scores_list.sort(key=lambda x: x["score"], reverse=True)
        high_scores[game_id] = scores_list[:5]

        _save_data(data)


def render_hall_of_fame():
    """Render Hall of Fame ASCII dashboard with player rankings and high scores."""
    with _LOCK:
        data = _load_data()

    players = data.get("players", {})
    high_scores = data.get("high_scores", {})
    recent = data.get("recent_matches", [])

    lines = [
        paint("=" * 64, "1;36"),
        paint("           🏆  C O L L E G E   L A N   A R C A D E  🏆", "1;36"),
        paint("                     H A L L   O F   F A M E", "1;33"),
        paint("=" * 64, "1;36"),
        "",
        paint("  TOP ARCADE CHAMPIONS (BY WINS):", "1;32"),
        paint("   Rank   Player Name             Wins    Losses    Win %    Streak", "2"),
        paint("   " + "-" * 58, "2")
    ]

    # Sort players by wins descending
    sorted_players = sorted(
        players.items(),
        key=lambda item: (item[1]["wins"], -item[1]["losses"]),
        reverse=True
    )

    if not sorted_players:
        lines.append("     No matches recorded yet. Host or join a match to claim #1!")
    else:
        for idx, (p_name, stat) in enumerate(sorted_players[:8], 1):
            tot = stat["games"]
            win_pct = f"{(stat['wins'] / tot * 100):.0f}%" if tot > 0 else "0%"
            medal = "🥇 " if idx == 1 else ("🥈 " if idx == 2 else ("🥉 " if idx == 3 else f"#{idx:<2}"))
            streak_str = f"🔥 {stat['streak']}" if stat["streak"] >= 2 else f"{stat['streak']}"
            lines.append(
                f"   {medal:<5} {p_name:<21} {stat['wins']:<7} {stat['losses']:<9} {win_pct:<8} {streak_str}"
            )

    # High score tables for 2048, Boggle, Scrabble Sprint
    if high_scores:
        lines.append("")
        lines.append(paint("  ALL-TIME RECORD HIGH SCORES:", "1;33"))
        for gid, scores in sorted(high_scores.items()):
            g_title = gid.replace("_", " ").title()
            lines.append(f"   ▶ {paint(g_title, '1;36')}:")
            for rank, entry in enumerate(scores[:3], 1):
                det = f" ({entry['detail']})" if entry.get("detail") else ""
                lines.append(
                    f"      #{rank} {entry['player']:<18} Score: {paint(str(entry['score']), '1;32')}{det}  [{entry['date']}]"
                )

    # Recent matches ticker
    if recent:
        lines.append("")
        lines.append(paint("  RECENT MATCHES:", "1;36"))
        for m in recent[:4]:
            win_txt = ", ".join(m["winners"]) if m["winners"] else "Draw"
            lines.append(f"   • {m['date']} | {m['game']} → Winner: {paint(win_txt, '1;32')}")

    lines.append("")
    lines.append(paint("=" * 64, "1;36"))
    return "\n".join(lines)
