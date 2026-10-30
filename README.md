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

## 🎲 Available Games

| # | Game | Players | Game Type | Objective / Description |
|---|---|---|---|---|
| **1** | **Bingo (1–25)** | 2–4 Players *(+ Solo vs PC)* | Number Calling | Call numbers 1–25 to complete lines on your 5x5 board. First to complete 5 lines to spell `B-I-N-G-O` wins! |
| **2** | **Connect Four** | 2 Players | Board Strategy | Drop tokens into a 6x7 grid. Connect 4 tokens in a row horizontally, vertically, or diagonally to win. |
| **3** | **Liar's Dice** | 2–4 Players | Bluffing & Hidden Dice | Reroll secret dice each round. Bid on total dice counts or call out opponents' bluffs. Last survivor wins! |
| **4** | **Battleship** | 2 Players | Hidden Grid Combat | Place a fleet of 3 ships on a hidden 5x5 grid. Take turns targeting coordinates (`A1`–`E5`) to sink the enemy fleet! |
| **5** | **UNO / Card Craze** | 2–4 Players | Card Shedding | Match color/symbol, play Skip, Reverse, +2, +4, and Wild cards. First to empty their hand wins! |
| **6** | **Dots and Boxes** | 2–4 Players | Territory Strategy | Connect dots on a grid to complete boxes. Claiming a box awards an extra turn! |
| **7** | **Tic-Tac-Toe** | 2 Players | Quick Grid Strategy | Take turns placing X or O on a 3x3 grid. Form 3 in a row to win! |
| **8** | **Mastermind** | 2 Players | Deductive Logic | Codemaker sets a 4-digit secret code; Codebreaker gets 10 attempts with Black/White peg feedback. |

---

## 🧪 Running Unit Tests

Run all unit tests using Python's built-in `unittest`:

```bash
python3 -m unittest discover -s tests
```
