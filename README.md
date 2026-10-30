# 🎮 College LAN Arcade

A modular, terminal-based multiplayer LAN game platform built in Python. Designed for playing games over college Wi-Fi/LAN networks without needing external internet access, databases, or third-party dependencies.

---

## 🌟 Features

- **Host-Authoritative Architecture**: The host machine manages game state, move validation, turn progression, and scoring.
- **Privacy Enforcement**: Private game information (e.g., hidden hands in UNO, hidden dice in Liar's Dice, hidden fleets in Battleship) is strictly filtered before being sent to individual player clients.
- **Unified Game Framework**: All games share the same TCP networking, room management, lobby system, and message protocol.
- **8 Supported Games**:
  1. **Bingo 1–25** (2–4 Players) - Number calling, complete line detection, solo vs PC mode, local pass-and-play.
  2. **Connect Four** (2 Players) - Classic 6x7 strategy board game.
  3. **Liar's Dice** (2–4 Players) - Bluffing, secret dice rolling, and bidding.
  4. **Battleship** (2 Players) - Hidden 5x5 grids and coordinate targeting.
  5. **UNO / Card Craze** (2–4 Players) - Card shedding with Skip, Reverse, Draw Two, Wild, and Wild Draw Four cards.
  6. **Dots and Boxes** (2–4 Players) - Connect grid dots to claim boxes and earn extra turns.
  7. **Tic-Tac-Toe** (2 Players) - Classic 3x3 strategy grid game.
  8. **Mastermind** (2 Players) - Deductive logic codebreaking.
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
- **Input Format**: Type a single number:
  - `12` or `5` or `25`

### 2. Connect Four
- **Rules**: Drop your token (`X` or `O`) into one of the 7 columns. First to connect 4 in a row horizontally, vertically, or diagonally wins.
- **Input Format**: Type the column number (1 to 7):
  - `3` or `1` or `7`

### 3. Liar's Dice
- **Rules**: Make a claim about the total count of a dice face across **ALL** players' secret hands (e.g. "three 4s"). 
  - To raise, bid a higher quantity (e.g. `4 4`) or higher face at same quantity (e.g. `3 5`).
  - If you think the previous bid is a lie, challenge it by typing `C`.
  - If the bid was truthful, the challenger loses 1 die. If it was a bluff, the bidder loses 1 die.
- **Input Format**:
  - To Bid: `<quantity> <face>` separated by a space (e.g. `2 1` for two 1s, or `3 4` for three 4s). Do **not** use quotes!
  - To Challenge: `C` or `challenge`

### 4. Battleship
- **Rules**: Target coordinates on the enemy's hidden 5x5 grid (Columns A–E, Rows 1–5). Sink all 3 enemy ships (7 total hits) to win.
- **Input Format**: Type column letter + row number:
  - `C3` or `A1` or `E5`

### 5. UNO / Card Craze
- **Rules**: Match the active card's color or value, or play a Wild card. First player to empty their hand wins.
  - Action Cards: `Skip`, `Reverse`, `+2`, `Wild`, `Wild +4`.
- **Input Format**:
  - Play Regular Card: Type the card number index from your list (e.g. `1` or `3`).
  - Play Wild Card: Type card index + chosen color (e.g. `1 Red` or `2 Blue`).
  - Draw Card: Type `D` or `draw`.

### 6. Dots and Boxes
- **Rules**: Place a horizontal (`H`) or vertical (`V`) edge on the grid. Completing a 1x1 box claims it with your symbol and awards an **extra turn**! Player with most claimed boxes wins.
- **Input Format**:
  - Horizontal Edge: `H <row> <col>` (e.g. `H 1 1` for row 1, col 1).
  - Vertical Edge: `V <row> <col>` (e.g. `V 2 3` for row 2, col 3).

### 7. Tic-Tac-Toe
- **Rules**: Alternate placing `X` or `O` on a 3x3 grid (cells 1 to 9). Form 3 in a row to win.
- **Input Format**: Type cell position (1 to 9):
  - `5` (center) or `1` (top-left) or `9` (bottom-right).

### 8. Mastermind
- **Rules**: Codemaker secretly sets a 4-digit code using numbers 1–6. Codebreaker gets 10 attempts to guess the exact 4 digits. Feedback gives `Black Pegs` (exact position & number) and `White Pegs` (correct number, wrong position).
- **Input Format**: 4 space-separated digits between 1 and 6:
  - Codemaker setting code: `1 4 2 6`
  - Codebreaker guessing: `1 2 3 4`

---

## 🧪 Running Unit Tests

Run all unit tests using Python's built-in `unittest`:

```bash
python3 -m unittest discover -s tests
```
