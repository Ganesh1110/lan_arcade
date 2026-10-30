# 🎮 College LAN Arcade

A modular, terminal-based multiplayer LAN game platform built in Python. Designed for playing games over college Wi-Fi/LAN networks without needing external internet access, databases, or third-party dependencies.

---

## 🌟 Features

- **Host-Authoritative Architecture**: The host machine manages game state, move validation, line detection, turn progression, and scoring.
- **Privacy Enforcement**: Private game information (e.g., hidden dice in Liar's Dice, hidden fleets in Battleship) is strictly filtered before being sent to individual player clients.
- **Unified Game Framework**: All games share the same TCP networking, room management, lobby system, and message protocol.
- **Multiple Supported Games**:
  1. **Bingo 1–25** (2–4 Players) - Number calling, complete line detection, solo vs PC mode, local pass-and-play.
  2. **Connect Four** (2 Players) - Classic 6x7 strategy board game.
  3. **Liar's Dice** (2–4 Players) - Bluffing, secret dice rolling, and bidding.
  4. **Battleship** (2 Players) - Hidden 5x5 grids and coordinate targeting.
- **Zero External Dependencies**: Runs entirely on Python 3.9+ standard library.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.9 or higher installed on all devices.
- All players connected to the same Wi-Fi / Local Area Network (LAN) or Mobile Hotspot.

### 2. Launch the Application

On the **Host** device:
```bash
python3 lan_core.py
```
1. Select `1. Host a LAN Game`.
2. Choose your game (`Bingo`, `Connect Four`, `Liar's Dice`, `Battleship`).
3. Note the displayed LAN IP address (e.g. `192.168.1.105`) and Port (`50555`).
4. Share the IP with your friends.
5. Once your friends join the lobby, press **Enter** to start!

On the **Client** devices (Friends):
```bash
python3 lan_core.py
```
1. Select `2. Join a LAN Game`.
2. Enter the Host's IP address and Port.
3. Choose your player name.
4. Wait in the lobby for the Host to start the game!

---

## 🎲 Available Games

### 1. Bingo (1–25)
- **Players**: 2–4
- **Rules**: Call unused numbers on your turn. Every completed row, column, or diagonal earns a letter in `B-I-N-G-O`. First to complete all 5 letters wins.
- **Single-Player Mode**: Includes a Solo mode to play against intelligent PC opponents.

### 2. Connect Four
- **Players**: 2
- **Rules**: Drop tokens into a 6x7 grid. Connect 4 tokens horizontally, vertically, or diagonally to win.

### 3. Liar's Dice
- **Players**: 2–4
- **Rules**: Each player starts with 5 secret dice. Players make bids on the total quantity of a dice face showing across all players. Challenge a bid if you think it's a bluff!

### 4. Battleship
- **Players**: 2
- **Rules**: Place your fleet on a hidden 5x5 grid. Call coordinates (`A1` to `E5`) to target and destroy the enemy fleet.

---

## 🛠️ Project Structure

```
lan_arcade/
│
├── lan_core.py          # Main application launcher and top-level menus
├── config.py            # Global settings, color definitions, and terminal utilities
├── protocol.py          # JSON message serialization and message types
├── README.md            # Documentation and user manual
│
├── core/                # Core networking and orchestration framework
│   ├── client.py        # Client connection session and background receiver thread
│   ├── server.py        # TCP server and authoritative host game orchestrator
│   ├── room.py          # Room state, player sessions, and message queue
│   ├── game_manager.py  # Bridge loading game engines into the network framework
│   ├── session.py       # Server-side player session data model
│   ├── renderer.py      # Common terminal UI rendering functions
│   └── exceptions.py   # Custom exception classes
│
├── games/               # Modular game implementations
│   ├── bingo.py         # Bingo engine (LAN multiplayer & Solo vs PC)
│   ├── connect4.py      # Connect Four strategy engine
│   ├── liars_dice.py    # Liar's Dice bluffing engine
│   └── battleship.py    # Battleship grid combat engine
│
├── utils/               # Utilities
│   ├── network.py       # LAN IP address auto-discovery
│   ├── validation.py    # Name and coordinate validation helpers
│   └── logger.py        # Application logging
│
└── tests/               # Comprehensive unit test suite
    ├── test_protocol.py
    ├── test_bingo.py
    ├── test_connect4.py
    ├── test_liars_dice.py
    └── test_battleship.py
```

---

## 🧪 Running Unit Tests

Run all unit tests using Python's built-in `unittest`:

```bash
python3 -m unittest discover -s tests
```

---

## 🔒 Wi-Fi & Firewall Troubleshooting

If your friends cannot connect to your host machine:
1. **Firewall Settings**: Ensure Python is allowed through your computer's OS firewall for inbound TCP connections on port `50555`.
2. **Client Isolation**: Some college Wi-Fi networks enable *Client Isolation*, which prevents devices on the network from talking directly to each other. If this is enabled, host a Wi-Fi hotspot from your mobile phone or laptop and have everyone connect to it.
