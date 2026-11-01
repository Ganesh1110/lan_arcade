# 🎮 College LAN Arcade

A modular, terminal-based multiplayer LAN game platform built in Python. Designed for playing games over college Wi-Fi/LAN networks without needing external internet access, databases, or third-party dependencies.

---

## 🌟 Features

- **Host-Authoritative Architecture**: The host machine manages game state, move validation, turn progression, and scoring.
- **Privacy Enforcement**: Private game information (e.g., secret word in Hangman, hidden fleets in Battleship) is strictly filtered before being sent to individual player clients.
- **Unified Game Framework**: All games share the same TCP networking, room management, lobby system, and message protocol.
- **7 Supported Games**:
  1. **Bingo 1–25** (2–4 Players) - Number calling, complete line detection, solo vs PC mode, local pass-and-play.
  2. **Connect Four** (2 Players) - Classic 6x7 strategy board game.
  3. **Battleship** (2 Players) - Hidden 5x5 grids and coordinate targeting.
  4. **Dots and Boxes** (2–4 Players) - Connect grid dots to claim boxes and earn extra turns.
  5. **Tic-Tac-Toe** (2 Players) - Classic 3x3 strategy grid game.
  6. **Hangman** (2 Players) - Word Master sets secret phrase; Guesser tries to guess letters with visual gallows.
  7. **Rock, Paper, Scissors** (2 Players) - Simultaneous choice Best-of-3 match.
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
2. Choose your game.
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

## 📖 How to Play & Input Format Guide

### 1. Bingo (1–25)
- **Rules**: Call an unused number from 1 to 25. Complete rows, columns, or diagonals to earn letters in `B-I-N-G-O`. First to spell all 5 letters wins.
- **Input Format**: Type a single number: `12` or `5` or `25`

### 2. Connect Four
- **Rules**: Drop your token (`X` or `O`) into one of the 7 columns. First to connect 4 in a row horizontally, vertically, or diagonally wins.
- **Input Format**: Type the column number (1 to 7): `3` or `1` or `7`

### 3. Battleship
- **Rules**: Target coordinates on the enemy's hidden 5x5 grid (Columns A–E, Rows 1–5). Sink all 3 enemy ships (7 total hits) to win.
- **Input Format**: Type column letter + row number: `C3` or `A1` or `E5`

### 4. Dots and Boxes
- **Rules**: Place a horizontal (`H`) or vertical (`V`) edge on the grid. Completing a 1x1 box claims it with your symbol and awards an **extra turn**! Player with most claimed boxes wins.
- **Input Format**:
  - Horizontal Edge: `H <row> <col>` (e.g. `H 1 1`).
  - Vertical Edge: `V <row> <col>` (e.g. `V 2 3`).

### 5. Tic-Tac-Toe
- **Rules**: Alternate placing `X` or `O` on a 3x3 grid (cells 1 to 9). Form 3 in a row to win.
- **Input Format**: Type cell position (1 to 9): `5` (center) or `1` (top-left) or `9` (bottom-right).

### 6. Hangman
- **Rules**: Word Master sets a secret word/phrase (A–Z). Guesser takes turns guessing single letters with visual ASCII gallows. Guesser wins if word is revealed before 6 wrong guesses!
- **Input Format**:
  - Setting Secret Word (Word Master): `COMPUTER` or `PYTHON`
  - Guessing Letter (Guesser): `E` or `A`

### 7. Rock, Paper, Scissors (Best of 3)
- **Rules**: Both players submit secret moves (`R` for Rock, `P` for Paper, `S` for Scissors). Moves reveal simultaneously. First player to 2 round wins wins the match!
- **Input Format**: Type `R` (Rock), `P` (Paper), or `S` (Scissors).

---

## 🧪 Running Unit Tests

Run all unit tests using Python's built-in `unittest`:

```bash
python3 -m unittest discover -s tests
```
