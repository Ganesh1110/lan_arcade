"""
Network helpers for LAN IP discovery.
"""
import socket


def get_lan_ip():
    """Discover local LAN IP address of host device."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()
