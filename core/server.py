"""
TCP Server and authoritative host game loop for LAN Arcade.
"""
import json
import socket
import socketserver
import threading
import time
from config import DEFAULT_PORT, paint, clear_screen, play_sound, TURN_TIMEOUT_SECONDS
from core.exceptions import InvalidMoveError
from core.game_manager import GameManager
from core.room import Room, SURRENDER_COMMANDS
from protocol import decode_message, encode_message
from utils.discovery import start_beacon
from utils.input import read_direct_key
from utils.network import get_lan_ip
from utils.stats import record_match_outcome, record_high_score
from utils.validation import clean_name


class LanTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, room):
        self.room = room
        super().__init__(address, LanRequestHandler)


class LanRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.server.room.client_handler(self.request)


def handle_surrender(room, gm, surr_pid):
    surr_p = room.get_player(surr_pid)
    surr_name = surr_p.name if surr_p else "Player"
    if surr_p:
        surr_p.has_surrendered = True
        surr_p.losses += 1

    # Active non-surrendered players
    active_remaining = [
        p for p in room.players
        if p.player_id != surr_pid and p.is_online and not getattr(p, "has_surrendered", False)
    ]

    # In 3-4 player games with 2+ players still competing, eliminate surrendering player and continue!
    if len(active_remaining) > 1:
        notice = f"🏳️ {surr_name} surrendered and is eliminated! Match continues with remaining players."
        room.log.append(notice)
        room.broadcast({"type": "notice", "message": notice})
        gm.skip_player(surr_pid)
        return False  # Match is not over

    winners = [p.name for p in active_remaining]
    msg = f"🏳️ {surr_name} surrendered the match! Winner(s): {', '.join(winners)}" if winners else f"🏳️ {surr_name} surrendered the match!"
    room.log.append(f"🏳️ {surr_name} surrendered the match!")

    for p in room.players:
        if winners and p.name in winners:
            p.wins += 1

    # Record persistent match stats and trigger audio
    record_match_outcome(room.game_module.game_name, [p.name for p in room.players], winners)
    play_sound("win")

    # Record high scores for score-based games
    if isinstance(gm.state, dict) and "scores" in gm.state:
        scores = gm.state["scores"]
        for p in room.players:
            if p.player_id in scores:
                sc = scores[p.player_id]
                if sc > 0:
                    detail = None
                    if room.game_module.game_id == "game2048":
                        max_t = gm.state.get("max_tiles", {}).get(p.player_id)
                        detail = f"Tile: {max_t}" if max_t else None
                    record_high_score(room.game_module.game_id, p.name, sc, detail)

    room.broadcast({
        "type": "end",
        "message": msg,
        "winners": winners,
        "players": room.players_payload()
    })

    clear_screen()
    final_host_view = gm.get_view_for(0)
    print(room.game_module.render_final(final_host_view, msg, winners))

    print("\n" + paint("=" * 48, "1;36"))
    print("  1. Rematch (Play Again with same players)")
    print("  2. Return to Main Menu")
    print(paint("=" * 48, "1;36"))

    choice = input("\nSelect option [1]: ").strip()
    if choice == "2":
        room.closed = True
        room.started = False
        room.broadcast({"type": "host_exit", "message": "Host returned to main menu."})
    else:
        room.broadcast({"type": "rematch", "message": "Host initiated a rematch!"})
        time.sleep(0.8)
        play_lan_host(room)
    return True


def play_lan_host(room):
    """Host authoritative main game loop."""
    room.started = True
    gm = GameManager(room.game_module)
    gm.initialize(room.players)

    # Reset surrender flag for all players at the start of each game/rematch
    for p in room.players:
        p.has_surrendered = False

    # Clean state for new game / rematch
    room.drain_moves()
    while not room.surrender_queue.empty():
        try:
            room.surrender_queue.get_nowait()
        except Exception:
            break
    room.log.clear()

    # Send initial game view payload to each client
    for p in room.players:
        if p.player_id != 0:
            view = gm.get_view_for(p.player_id)
            room.send(p.player_id, {
                "type": "start",
                "you": p.player_id,
                "name": p.name,
                "game_id": room.game_module.game_id,
                "view": view,
                "players": room.players_payload()
            })

    while not gm.is_over():
        if not room.surrender_queue.empty():
            surr_pid = room.surrender_queue.get()
            if handle_surrender(room, gm, surr_pid):
                return
            continue

        # Check if active online players remain
        active_clients = [
            p for p in room.players
            if (p.player_id == 0 or p.player_id in room.connections) and not getattr(p, "has_surrendered", False)
        ]
        if len(active_clients) < room.min_players and len(room.players) > 1:
            print("\nNot enough players remaining. Game ending.")
            room.broadcast({"type": "end", "message": "Game ended: Not enough players remaining."})
            return

        current_pid = gm.current_player_id()
        current_player = room.get_player(current_pid)

        # Skip if current player disconnected or has surrendered
        if getattr(current_player, "has_surrendered", False) or (current_pid != 0 and current_pid not in room.connections):
            status_txt = "has surrendered" if getattr(current_player, "has_surrendered", False) else "is offline"
            room.log.append(f"{current_player.name} {status_txt} — turn passed.")
            gm.skip_player(current_pid)
            continue

        room.drain_moves()

        # Broadcast turn update to all clients with updated individual views
        for p in room.players:
            if p.player_id in room.connections:
                view = gm.get_view_for(p.player_id)
                room.send(p.player_id, {
                    "type": "turn",
                    "player_id": current_pid,
                    "player_name": current_player.name,
                    "game_id": room.game_module.game_id,
                    "view": view,
                    "players": room.players_payload()
                })

        # Render host UI
        clear_screen()
        host_view = gm.get_view_for(0)
        host_view["log"] = list(room.log)
        print(room.game_module.render_dashboard(host_view))

        action_data = None
        play_sound("turn")
        if current_pid == 0:
            # Host's local turn
            prompt_str = gm.get_prompt_for(0)
            while True:
                if not room.surrender_queue.empty():
                    surr_pid = room.surrender_queue.get()
                    if handle_surrender(room, gm, surr_pid):
                        return
                    break

                if getattr(room.game_module, "direct_input", False):
                    print(f"\n  ▶ YOUR TURN ({current_player.name}) — [Steer with W/A/S/D or Arrow Keys]: ", end="", flush=True)
                    raw_in = None
                    while raw_in is None:
                        if not room.surrender_queue.empty():
                            surr_pid = room.surrender_queue.get()
                            if handle_surrender(room, gm, surr_pid):
                                return
                            break
                        raw_in = read_direct_key(timeout=0.2)
                else:
                    raw_in = input(f"\n  ▶ YOUR TURN ({current_player.name}) — {prompt_str} (or '!ff' to give up, '! <msg>' to chat): ").strip()

                if str(raw_in).lower() in SURRENDER_COMMANDS:
                    if handle_surrender(room, gm, 0):
                        return
                    break
                if str(raw_in).startswith("!"):
                    msg = str(raw_in)[1:].strip()
                    if msg.lower() in {"ff", "surrender", "giveup", "quit", "exit", "resign"}:
                        if handle_surrender(room, gm, 0):
                            return
                        break
                    if msg:
                        entry = f"💬 {current_player.name}: {msg}"
                        room.log.append(entry)
                        room.broadcast({"type": "chat", "sender": current_player.name, "text": msg, "entry": entry})
                        clear_screen()
                        host_view["log"] = list(room.log)
                        print(room.game_module.render_dashboard(host_view))
                    continue

                valid, result_or_err = room.game_module.parse_action(gm.state, 0, raw_in)
                if valid:
                    action_data = result_or_err
                    break
                print(paint(f"  ! {result_or_err}", "1;31"))
        else:
            # Remote player's turn
            print(f"\n  Waiting for {current_player.name}... (Type '!ff' to give up, '! <msg>' to chat)")
            turn_start_time = time.time()
            turn_limit = getattr(room.game_module, "turn_timeout", TURN_TIMEOUT_SECONDS)
            while True:
                if not room.surrender_queue.empty():
                    surr_pid = room.surrender_queue.get()
                    if handle_surrender(room, gm, surr_pid):
                        return
                    break

                elapsed = time.time() - turn_start_time
                if elapsed > turn_limit:
                    timeout_msg = f"⏳ {current_player.name} timed out ({turn_limit}s) — auto-gliding forward."
                    room.log.append(timeout_msg)
                    room.broadcast({"type": "notice", "message": timeout_msg})
                    gm.skip_player(current_pid)
                    break

                try:
                    pid, raw_act = room.incoming_moves.get(timeout=0.5)
                except Exception:
                    if current_pid not in room.connections:
                        break
                    continue

                if not room.surrender_queue.empty():
                    surr_pid = room.surrender_queue.get()
                    if handle_surrender(room, gm, surr_pid):
                        return
                    break

                if str(raw_act).strip().lower() in SURRENDER_COMMANDS:
                    if handle_surrender(room, gm, pid):
                        return
                    break

                if pid != current_pid:
                    room.send(pid, {"type": "error", "message": "It is not your turn."})
                    continue

                valid, result_or_err = room.game_module.parse_action(gm.state, current_pid, raw_act)
                if not valid:
                    room.send(pid, {"type": "error", "message": str(result_or_err)})
                    continue

                action_data = result_or_err
                break

        if action_data is None:
            continue

        # Apply action
        events = gm.apply_action(current_pid, action_data)
        if events and isinstance(events, dict) and "log" in events:
            for log_entry in events["log"]:
                room.log.append(log_entry)

        # Broadcast outcome action update and new views
        for p in room.players:
            if p.player_id in room.connections:
                v = gm.get_view_for(p.player_id)
                v["log"] = list(room.log)
                room.send(p.player_id, {
                    "type": "action_result",
                    "caller": current_player.name,
                    "game_id": room.game_module.game_id,
                    "view": v,
                    "events": events,
                    "players": room.players_payload()
                })

    # Game Over
    winners = gm.get_winner()
    msg = f"Winner(s): {', '.join(winners)}" if winners else "Game Over - Draw!"

    # Award Stats
    for p in room.players:
        if winners and p.name in winners:
            p.wins += 1
        elif winners:
            p.losses += 1

    # Record persistent match stats and trigger audio
    record_match_outcome(room.game_module.game_name, [p.name for p in room.players], winners)
    play_sound("win")

    # Record high scores for score-based games
    if isinstance(gm.state, dict) and "scores" in gm.state:
        scores = gm.state["scores"]
        for p in room.players:
            if p.player_id in scores:
                sc = scores[p.player_id]
                if sc > 0:
                    detail = None
                    if room.game_module.game_id == "game2048":
                        max_t = gm.state.get("max_tiles", {}).get(p.player_id)
                        detail = f"Tile: {max_t}" if max_t else None
                    record_high_score(room.game_module.game_id, p.name, sc, detail)

    room.broadcast({
        "type": "end",
        "message": msg,
        "winners": winners,
        "players": room.players_payload()
    })

    clear_screen()
    final_host_view = gm.get_view_for(0)
    print(room.game_module.render_final(final_host_view, msg, winners))

    print("\n" + paint("=" * 48, "1;36"))
    print("  1. Rematch (Play Again with same players)")
    print("  2. Return to Main Menu")
    print(paint("=" * 48, "1;36"))

    choice = input("\nSelect option [1]: ").strip()
    if choice == "2":
        room.closed = True
        room.started = False
        room.broadcast({"type": "host_exit", "message": "Host returned to main menu."})
        return
    else:
        room.broadcast({"type": "rematch", "message": "Host initiated a rematch!"})
        time.sleep(0.8)
        play_lan_host(room)


def render_host_lobby(room, host_ip, port):
    lines = [
        paint("=" * 56, "1;36"),
        paint(f"       LAN {room.game_module.game_name.upper()} HOST LOBBY", "1;36"),
        paint("=" * 56, "1;36"),
        "",
        f"  Host IP address : {paint(host_ip, '1;33')}",
        f"  Port            : {paint(port, '1;33')}",
        f"  Required Players: {room.min_players}–{room.max_players} players",
        "",
        f"  Connected Players ({len(room.players)}/{room.max_players}):"
    ]
    with room.lock:
        for i, p in enumerate(room.players, 1):
            host_tag = " " + paint("[HOST]", "1;33") if p.is_host else ""
            ready_tag = " " + paint("[READY]", "1;32") if p.is_ready else " " + paint("[WAITING]", "31")
            lines.append(f"    {i}. {p.name:<20}{host_tag}{ready_tag}")
    lines.append("")
    lines.append(paint("-" * 56, "2"))
    lines.append("  Commands:")
    lines.append("    • Press [ENTER] to start match (once friends join)")
    lines.append("    • Type 'R' to refresh player list")
    lines.append("    • Type 'Q' to cancel host and return to menu")
    lines.append(paint("=" * 56, "1;36"))
    return "\n".join(lines)


def host_lan_game_session(game_module):
    clear_screen()
    print(paint("=" * 56, "1;36"))
    print(paint(f"         HOST LAN: {game_module.game_name.upper()}", "1;36"))
    print(paint("=" * 56, "1;36"))
    print("")
    raw_name = input("  Enter your player name (or 'q' to cancel): ").strip()
    if raw_name.lower() in {"q", "quit", "cancel", "back", "exit"}:
        return

    host_name = clean_name(raw_name, "Host")
    room = Room(host_name, game_module)

    server = None
    bound_port = DEFAULT_PORT

    # Attempt to bind to DEFAULT_PORT; if busy, auto-fallback to next open ports
    for try_port in range(DEFAULT_PORT, DEFAULT_PORT + 20):
        try:
            server = LanTCPServer(("0.0.0.0", try_port), room)
            bound_port = try_port
            break
        except OSError:
            continue

    if server is None:
        clear_screen()
        print(paint(f"\n[!] Could not start host on ports {DEFAULT_PORT}–{DEFAULT_PORT + 20}.", "1;31"))
        print("    Another game server or process is already using these ports.")
        input("\nPress Enter to return to main menu...")
        return

    threading.Thread(target=server.serve_forever, daemon=True).start()
    host_ip = get_lan_ip()

    # Start LAN discovery beacon
    beacon_stop = None
    try:
        beacon_stop = start_beacon(
            f"{host_name}'s Room",
            game_module.game_name,
            bound_port,
            lambda: len(room.players),
            room.max_players
        )
    except Exception:
        pass

    try:
        while True:
            clear_screen()
            print(render_host_lobby(room, host_ip, bound_port))
            if bound_port != DEFAULT_PORT:
                print(paint(f"\n  Notice: Port {DEFAULT_PORT} was busy; hosted on port {bound_port} instead.", "1;33"))
                print(f"  Tell players to join with port: {paint(bound_port, '1;33')}")

            cmd = input("\nEnter command [ENTER to start]: ").strip().lower()
            if cmd in {"q", "quit", "exit", "cancel", "back"}:
                print("\nHost cancelled lobby. Returning to main menu...")
                time.sleep(0.5)
                return

            if cmd in {"r", "refresh"}:
                continue

            with room.lock:
                if len(room.players) >= room.min_players:
                    room.started = True
                    names = room.player_names()
                    break
                else:
                    curr_cnt = len(room.players)
                    req_cnt = room.min_players
                    print(paint(f"\n[!] Need at least {req_cnt} players to start (currently {curr_cnt} joined).", "1;31"))
                    print(f"    Ask friends to run '2. Join a LAN Game' connecting to {host_ip}:{bound_port}")
                    input("\nPress Enter to continue waiting...")

        clear_screen()
        print("\n" + paint("=" * 56, "1;32"))
        print(paint("  Starting game! Players: " + " → ".join(names), "1;32"))
        print(paint("=" * 56, "1;32"))
        time.sleep(1.0)
        play_lan_host(room)
    except KeyboardInterrupt:
        print("\nHost stopped the game.")
        room.broadcast({"type": "end", "message": "Host stopped the game."})
    finally:
        room.closed = True
        if beacon_stop is not None:
            try:
                beacon_stop.set()
            except Exception:
                pass
        time.sleep(0.2)
        try:
            server.shutdown()
            server.server_close()
        except Exception:
            pass


def run_dedicated_server(port=DEFAULT_PORT):
    """Run dedicated office arcade server listening 24/7."""
    from games import bingo
    room = Room("OfficeServer", bingo)
    try:
        server = LanTCPServer(("0.0.0.0", port), room)
    except OSError as exc:
        print(f"Could not start dedicated server on port {port}: {exc}")
        return

    print("\n" + paint("DEDICATED OFFICE LAN ARCADE SERVER IS RUNNING", "1;32"))
    print(f"  Server Address : {paint(get_lan_ip(), '1;33')}")
    print(f"  Listening Port : {paint(port, '1;33')}")
    print("\nPlayers can connect from their PCs using 'python3 lan_core.py' -> '2. Join a LAN Game'.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDedicated server stopped.")
    finally:
        server.shutdown()
        server.server_close()
