"""
LAN Auto-Discovery using lightweight UDP beacon broadcasting.
Allows players on the same Wi-Fi/subnet to discover active game hosts without manual IP typing.
"""
import json
import socket
import threading
import time
from config import DEFAULT_DISCOVERY_PORT
from utils.network import get_lan_ip


def start_beacon(room_name, game_name, port, get_player_count_fn, max_players, broadcast_port=DEFAULT_DISCOVERY_PORT):
    """
    Launch a background daemon thread that broadcasts presence beacons every second.
    Returns a threading.Event that can be set to stop the beacon.
    """
    stop_event = threading.Event()

    def beacon_worker():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1.0)
        lan_ip = get_lan_ip()

        while not stop_event.is_set():
            try:
                curr_players = get_player_count_fn() if callable(get_player_count_fn) else get_player_count_fn
                payload = {
                    "type": "arcade_beacon",
                    "room": room_name,
                    "game": game_name,
                    "ip": lan_ip,
                    "port": port,
                    "players": curr_players,
                    "max": max_players
                }
                data = json.dumps(payload).encode("utf-8")
                # Broadcast on loopback and standard subnet broadcast addresses
                for target_ip in ["127.0.0.1", "255.255.255.255", "<broadcast>"]:
                    try:
                        sock.sendto(data, (target_ip, broadcast_port))
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(1.0)

        sock.close()

    thread = threading.Thread(target=beacon_worker, daemon=True)
    thread.start()
    return stop_event


def discover_hosts(timeout=1.5, broadcast_port=DEFAULT_DISCOVERY_PORT):
    """
    Listen for active LAN arcade beacons on the local network for `timeout` seconds.
    Returns list of discovered host dictionaries.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception:
            pass

    try:
        sock.bind(("0.0.0.0", broadcast_port))
    except Exception:
        # If unable to bind (e.g. strict firewall), return empty list cleanly
        sock.close()
        return []

    sock.settimeout(0.3)
    found_rooms = {}  # (ip, port) -> room dict
    t_end = time.time() + timeout

    while time.time() < t_end:
        try:
            data, addr = sock.recvfrom(2048)
            msg = json.loads(data.decode("utf-8", errors="ignore"))
            if msg.get("type") == "arcade_beacon":
                host_ip = msg.get("ip") or addr[0]
                host_port = msg.get("port")
                key = (host_ip, host_port)
                found_rooms[key] = {
                    "room": msg.get("room", "LAN Arcade Room"),
                    "game": msg.get("game", "Game"),
                    "ip": host_ip,
                    "port": host_port,
                    "players": msg.get("players", 1),
                    "max": msg.get("max", 4)
                }
        except (socket.timeout, json.JSONDecodeError, UnicodeDecodeError):
            continue
        except Exception:
            break

    sock.close()
    return list(found_rooms.values())
