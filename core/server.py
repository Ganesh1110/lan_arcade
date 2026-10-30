"""
TCP Server and authoritative host game loop for LAN Arcade.
"""
import json
import socket
import socketserver
import threading
import time
from config import DEFAULT_PORT, paint, clear_screen
from core.exceptions import InvalidMoveError
from core.game_manager import GameManager
from core.room import Room
from protocol import decode_message, encode_message
from utils.network import get_lan_ip
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


def play_lan_host(room):
    """Host authoritative main game loop."""
    gm = GameManager(room.game_module)
    gm.initialize(room.players)

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
        # Check if active online players remain
        active_clients = [p for p in room.players if p.player_id == 0 or p.player_id in room.connections]
        if len(active_clients) < room.min_players and len(room.players) > 1:
            print("\nNot enough players remaining. Game ending.")
            room.broadcast({"type": "end", "message": "Game ended: Not enough players remaining."})
            return

        current_pid = gm.current_player_id()
        current_player = room.get_player(current_pid)

        # Skip if current player disconnected
        if current_pid != 0 and current_pid not in room.connections:
            room.log.append(f"{current_player.name} is offline — turn skipped.")
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
                    "view": view,
                    "players": room.players_payload()
                })

        # Render host UI
        clear_screen()
        host_view = gm.get_view_for(0)
        host_view["log"] = list(room.log)
        print(room.game_module.render_dashboard(host_view))

        action_data = None
        if current_pid == 0:
            # Host's local turn
            prompt_str = gm.get_prompt_for(0)
            while True:
                raw_in = input(f"\n  ▶ YOUR TURN ({current_player.name}) — {prompt_str}: ").strip()
                if raw_in.lower() in {"q", "quit"}:
                    print("Ending game...")
                    room.broadcast({"type": "end", "message": "Host ended the game."})
                    return
                valid, result_or_err = room.game_module.parse_action(gm.state, 0, raw_in)
                if valid:
                    action_data = result_or_err
                    break
                print(paint(f"  ! {result_or_err}", "1;31"))
        else:
            # Remote player's turn
            print(f"\n  Waiting for {current_player.name}... (Ctrl+C to quit host)")
            while True:
                try:
                    pid, raw_act = room.incoming_moves.get(timeout=0.5)
                except Exception:
                    if current_pid not in room.connections:
                        break
                    continue

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
                    "view": v,
                    "events": events,
                    "players": room.players_payload()
                })

    # Game Over
    winners = gm.get_winner()
    msg = f"Winner(s): {', '.join(winners)}" if winners else "Game Over - Draw!"
    room.broadcast({
        "type": "end",
        "message": msg,
        "winners": winners
    })

    clear_screen()
    final_host_view = gm.get_view_for(0)
    print(room.game_module.render_final(final_host_view, msg, winners))


def host_lan_game_session(game_module):
    host_name = clean_name(input("Your player name: "), "Host")
    room = Room(host_name, game_module)
    try:
        server = LanTCPServer(("0.0.0.0", DEFAULT_PORT), room)
    except OSError as exc:
        print(f"Could not start the host on port {DEFAULT_PORT}: {exc}")
        print("Is another game already hosted on this computer?")
        return

    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("\n" + paint(f"LAN {game_module.game_name.upper()} HOST IS READY", "1;32"))
    print(f"  Host address : {paint(get_lan_ip(), '1;33')}")
    print(f"  Port         : {paint(DEFAULT_PORT, '1;33')}")
    print(f"\nShare IP with friends on same Wi-Fi ({room.min_players}–{room.max_players} players required).")

    try:
        while True:
            input("\nPress Enter to start the game once everyone has joined...")
            with room.lock:
                if len(room.players) >= room.min_players:
                    room.started = True
                    names = room.player_names()
                    break
            print(f"Need at least {room.min_players} players to start. Currently {len(room.players)} joined.")

        print("\nStarting game! Players: " + " → ".join(names))
        time.sleep(1.0)
        play_lan_host(room)
    except KeyboardInterrupt:
        print("\nHost stopped the game.")
        room.broadcast({"type": "end", "message": "Host stopped the game."})
    finally:
        room.closed = True
        time.sleep(0.2)
        server.shutdown()
        server.server_close()
