# 🎮 College LAN Arcade

A modular, terminal-based multiplayer LAN game platform built in Python. Designed for playing games over college Wi-Fi/LAN networks without needing external internet access, databases, or third-party dependencies.

---

## 🏢 Central Server Deployment (Zero-Installation for Students)

You can host **College LAN Arcade on a single central server** so that students across the entire campus can play **without downloading the repo or installing Python**!

### Method 1: Web Browser Access (`http://<server-ip>:8220`) ⭐ (Easiest for Everyone)
With Web Terminal (`ttyd`), any student on the college Wi-Fi opens Chrome/Safari on their laptop, tablet, or phone, goes to `http://<server-ip>:8220`, and gets the Arcade menu directly in their browser!

**Deploy via Docker Compose on your Central Server**:
```bash
git clone https://github.com/Ganesh1110/lan_arcade.git
cd lan_arcade
docker compose up -d
```
- Web Arcade URL: `http://<your-server-ip>:8220`
- Dedicated TCP Arcade Port: `50555`

---

### Method 2: One-Command SSH Access (`ssh arcade@<server-ip>`)
You can configure a restricted guest SSH user `arcade` on your central server whose default login shell is `python3 lan_core.py`.

Students simply open their terminal and type:
```bash
ssh arcade@<your-server-ip>
```
Password: `arcade` (or passwordless guest login).
The arcade menu launches instantly in their terminal with zero repo downloading required!

---

## 🌟 Features

- **Host-Authoritative Architecture**: The host machine manages game state, move validation, turn progression, and scoring.
- **Privacy Enforcement**: Private game information (e.g., secret word in Hangman, hidden fleets in Battleship) is strictly filtered before being sent to individual player clients.
- **Unified Game Framework**: All games share the same TCP networking, room management, lobby system, and message protocol.
- **21 Supported Games**:
  1. **Bingo 1–25** (2–4 Players) - Number calling, complete line detection, solo vs PC mode, local pass-and-play.
  2. **Connect Four** (2 Players) - Classic 6x7 strategy board game.
  3. **Battleship** (2 Players) - Hidden 5x5 grids and coordinate targeting.
  4. **Dots and Boxes** (2–4 Players) - Connect grid dots to claim boxes and earn extra turns.
  5. **Tic-Tac-Toe** (2 Players) - Classic 3x3 strategy grid game.
  6. **Hangman** (2 Players) - Word Master sets secret word/phrase; Guesser tries to guess letters with visual gallows.
  7. **Word Chain / Shiritori** (2–4 Players) - Word association with 3 lives per player.
  8. **2048 Versus** (2 Players) - Competitive 4x4 tile-merging race to the 2048 tile.
  9. **Boggle / Word Hunt** (2–4 Players) - 4x4 grid letter search.
  10. **Mini Crossword Race** (2 Players) - 5x5 speed crossword with Across and Down clues.
  11. **Wordoku** (2 Players) - 6x6 mini Sudoku deduction.
  12. **Anagram Showdown** (2–4 Players) - 7-letter speed anagram solver.
  13. **Snake & Ladders** (2–4 Players) - Classic 1–100 board game with ladders, snakes, dice rolling, extra turn on 6, and exact 100 roll win.
  14. **Wordle Duel** (2 Players) - 5-letter word guessing with color feedback.
  15. **Scrabble Sprint** (2 Players) - Speed word formation from letter racks.
  16. **Quiz Show** (2–4 Players) - Trivia competition across tech, CS, science, and pop culture.
  17. **Typing Racer** (2–4 Players) - Multiplayer speed typing race with real-time accuracy and WPM.
  18. **Artillery Duel** (2 Players) - Turn-based ballistic trajectories with wind and destructible terrain.
  19. **Snake Duel** (2 Players) - Tron-style grid slither duel with fruit growth.
  20. **Chess** (2 Players) - Full 8x8 standard chess with checkmate, castling, en passant, and promotion.
  21. **Arrow Man Duel** (2 Players) - Turn-based bowman archery duel with dynamic wind, special quivers, and randomized tower elevations.
- **In-Game Forfeit / Surrender & Live Chat**: Any player can type `!ff` / `!surrender` / `!giveup` / `!quit` at any time to forfeit a match, or `! <message>` to chat with room players.
- **Zero External Dependencies**: Runs entirely on Python 3.9+ standard library.

---

## 📖 How to Play & Input Format Guide

### 1. Bingo (1–25)
- **Rules**: Call an unused number from 1 to 25. Complete rows, columns, or diagonals to earn letters in `B-I-N-G-O`. First to spell all 5 letters wins.
- **Input Format**: `12` or `5` or `25`

### 2. Connect Four
- **Rules**: Drop your token (`X` or `O`) into one of the 7 columns. First to connect 4 in a row horizontally, vertically, or diagonally wins.
- **Input Format**: `3` or `1` or `7`

### 3. Battleship
- **Rules**: Target coordinates on the enemy's hidden 5x5 grid (Columns A–E, Rows 1–5). Sink all 3 enemy ships (7 total hits) to win.
- **Input Format**: `C3` or `A1` or `E5`

### 4. Dots and Boxes
- **Rules**: Place a horizontal (`H`) or vertical (`V`) edge on the grid. Completing a 1x1 box claims it with your symbol and awards an **extra turn**! Player with most claimed boxes wins.
- **Input Format**:
  - Horizontal Edge: `H <row> <col>` (e.g. `H 1 1`).
  - Vertical Edge: `V <row> <col>` (e.g. `V 2 3`).

### 5. Tic-Tac-Toe
- **Rules**: Alternate placing `X` or `O` on a 3x3 grid (cells 1 to 9). Form 3 in a row to win.
- **Input Format**: `5` (center) or `1` (top-left) or `9` (bottom-right).

### 6. Hangman
- **Rules**: Word Master sets a secret word/phrase (A–Z). Guesser takes turns guessing single letters with visual ASCII gallows.
- **Input Format**:
  - Setting Word: `COMPUTER`
  - Guessing Letter: `E` or `A`

### 7. Word Chain (Shiritori)
- **Rules**: Type a word starting with the last letter of the previous player's word (e.g., `APPLE` $\rightarrow$ `ELEPHANT` $\rightarrow$ `TIGER`). Entering a wrong starting letter or duplicate word deducts 1 life (`❤️`). Last surviving player wins!
- **Input Format**: Type a valid word (e.g. `ELEPHANT` or `TIGER`).

### 8. 2048 Versus
- **Rules**: Shift 4x4 tiles in direction `W` (Up), `A` (Left), `S` (Down), or `D` (Right). Equal tiles merge and double! First player to reach 2048 tile (or highest score) wins!
- **Input Format**: `W`, `A`, `S`, or `D`.

### 9. Snake & Ladders (1–100)
- **Rules**: Take turns rolling a 6-sided die to advance across a 100-square board. Climb ladders to jump ahead, watch out for snakes sliding you down! Rolling a 6 grants an **extra turn**. First to reach Square 100 (exact roll required) wins!
- **Input Format**: Press `[ENTER]` or type `r` to roll.

---

## 🔒 Network Architecture & Security Note

- **Open LAN Design**: College LAN Arcade binds its TCP socket server to `0.0.0.0` (all local network interfaces) on port `50555` with UDP broadcast beacon discovery to enable zero-configuration, friction-free peer joining without credentials.
- **Trusted Networks**: By design for campus dorms and hackathons, there is no transport encryption or authentication layer. Anyone connected to the same local subnet / Wi-Fi can discover and join open lobbies.
- **Buffer Safety**: Sockets enforce a strict 64 KB line length limit (`reader.readline(65536)`) to safeguard against buffer exhaustion, and in-game lobby commands (`!game`) are strictly restricted to the host before a match begins.
- If hosting on a multi-homed or exposed machine, ensure firewall rules or Docker network isolation limit access to trusted peers.

---

## 🧪 Running Unit Tests

Run all unit tests using Python's built-in `unittest`:

```bash
python3 -m unittest discover -s tests
```
