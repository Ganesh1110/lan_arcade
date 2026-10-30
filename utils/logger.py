"""
Simple logging utility for arcade server and client events.
"""
import sys
import time


def _log(level, msg):
    timestamp = time.strftime("%H:%M:%S")
    sys.stderr.write(f"[{timestamp}] [{level}] {msg}\n")
    sys.stderr.flush()


def log_info(msg):
    _log("INFO", msg)


def log_error(msg):
    _log("ERROR", msg)


def log_debug(msg):
    _log("DEBUG", msg)
