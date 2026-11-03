"""
Solo and Offline Practice Modes for College LAN Arcade.
Allows single players to enjoy games against intelligent bots or in high-score chase mode.
"""
import random
import time
from config import clear_screen, paint, play_sound
from games import (
    connect4, tic_tac_toe, battleship, snake_and_ladder, game2048, shiritori,
    wordle, quiz_show, typing_racer
)
from utils.dictionary import get_words_set
from utils.stats import record_high_score, record_match_outcome
from utils.validation import clean_name


# ==========================================
# 1. SOLO 2048 ENDLESS CHASE
# ==========================================
def run_solo_2048():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("         2048 — SOLO HIGH-SCORE CHASE", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    grid = game2048.create_initial_grid()
    score = 0
    moves = 0
    log = ["🎮 Use W (Up), A (Left), S (Down), D (Right) or 'Q' to quit."]

    while True:
        clear_screen()
        max_t = max(max(row) for row in grid)
        print(paint("=" * 50, "1;36"))
        print(paint(f"        2 0 4 8   S O L O   —   {name.upper()}", "1;36"))
        print(paint("=" * 50, "1;36"))
        print(f"\n  Score: {paint(score, '1;32')}    Max Tile: {paint(max_t, '1;33')}    Moves: {moves}")

        border = "  ┌─────┬─────┬─────┬─────┐"
        mid_b  = "  ├─────┼─────┼─────┼─────┤"
        bot_b  = "  └─────┴─────┴─────┴─────┘"

        print(border)
        for r in range(4):
            cells = [game2048._format_cell(grid[r][c]) for c in range(4)]
            print("  │" + "│".join(cells) + "│")
            if r < 3:
                print(mid_b)
            else:
                print(bot_b)

        if not game2048.can_move(grid):
            play_sound("win")
            print(paint("\n  💀 GAME OVER! No legal moves remaining.", "1;31"))
            print(f"  Final Score: {paint(score, '1;32')} | Highest Tile: {paint(max_t, '1;33')}")
            record_high_score("game2048", name, score, f"Tile: {max_t}")
            input("\nPress Enter to return to solo menu...")
            break

        if log:
            print("\n  " + log[-1])

        raw_in = input("\n  Shift (W/A/S/D) or 'Q' to save & exit: ").strip().upper()
        if raw_in in {"Q", "QUIT", "EXIT"}:
            record_high_score("game2048", name, score, f"Tile: {max_t}")
            print(paint(f"\n  Progress saved! Final Score: {score}", "1;32"))
            time.sleep(1.0)
            break

        if raw_in not in {"W", "A", "S", "D"}:
            log.append("Invalid direction. Use W, A, S, or D.")
            continue

        new_grid, changed, gain = game2048.move_grid(grid, raw_in)
        if changed:
            game2048.spawn_tile(new_grid)
            grid = new_grid
            score += gain
            moves += 1
            log.append(f"Shifted {raw_in} (+{gain} pts).")
            if max_t < 2048 and max(max(row) for row in grid) >= 2048:
                play_sound("win")
                log.append("🎉 CONGRATULATIONS! You reached the 2048 tile!")
        else:
            log.append(f"No tiles moved in direction {raw_in}.")


# ==========================================
# 2. CONNECT FOUR VS SMART BOT
# ==========================================
def _get_best_c4_col(board, bot_sym, player_sym):
    # 1. Winning move for Bot
    for c in range(connect4.COLS):
        if board[0][c] is None:
            r = max(row for row in range(connect4.ROWS) if board[row][c] is None)
            board[r][c] = bot_sym
            won, _ = connect4.check_win(board, r, c, bot_sym)
            board[r][c] = None
            if won:
                return c

    # 2. Block Player's winning move
    for c in range(connect4.COLS):
        if board[0][c] is None:
            r = max(row for row in range(connect4.ROWS) if board[row][c] is None)
            board[r][c] = player_sym
            won, _ = connect4.check_win(board, r, c, player_sym)
            board[r][c] = None
            if won:
                return c

    # 3. Prefer center columns
    preferred = [3, 2, 4, 1, 5, 0, 6]
    for c in preferred:
        if board[0][c] is None:
            return c
    return 0


def run_connect4_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("        CONNECT FOUR — VS ARCADE BOT", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    sessions = [{"id": 0, "name": name}, {"id": 1, "name": "ArcadeBot 🤖"}]
    state = connect4.create_state(sessions)

    while not connect4.is_over(state):
        curr_id = connect4.current_player(state)
        v = connect4.view_for(state, 0)
        v["log"] = state.get("log", [])
        clear_screen()
        print(connect4.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input(f"\n  ▶ YOUR TURN ({name}) — Choose column (1–7) or 'q' to quit: ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, col_idx = connect4.parse_action(state, 0, raw)
                if valid:
                    events = connect4.apply_action(state, 0, col_idx)
                    state["log"] = events.get("log", [])
                    break
                print(paint(f"  ! {col_idx}", "1;31"))
        else:
            print("\n  🤖 ArcadeBot is calculating next move...")
            time.sleep(0.8)
            board = state["board"]
            bot_col = _get_best_c4_col(board, "O", "X")
            events = connect4.apply_action(state, 1, bot_col)
            state["log"] = events.get("log", [])

    clear_screen()
    v = connect4.view_for(state, 0)
    winners = connect4.get_winner(state)
    msg = f"Winner: {', '.join(winners)}" if winners else "Game Over - Draw!"
    print(connect4.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Connect Four (vs Bot)", [name, "ArcadeBot 🤖"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 3. TIC-TAC-TOE VS BOT
# ==========================================
def _get_best_ttt_cell(board, bot_sym, player_sym):
    # 1. Win if possible
    for i in range(9):
        if board[i] is None:
            board[i] = bot_sym
            won, _ = tic_tac_toe.check_win(board, bot_sym)
            board[i] = None
            if won:
                return i

    # 2. Block opponent
    for i in range(9):
        if board[i] is None:
            board[i] = player_sym
            won, _ = tic_tac_toe.check_win(board, player_sym)
            board[i] = None
            if won:
                return i

    # 3. Center
    if board[4] is None:
        return 4

    # 4. Corners
    corners = [0, 2, 6, 8]
    random.shuffle(corners)
    for c in corners:
        if board[c] is None:
            return c

    # 5. Edges
    edges = [1, 3, 5, 7]
    for e in edges:
        if board[e] is None:
            return e
    return 0


def run_tic_tac_toe_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("        TIC-TAC-TOE — VS ARCADE BOT", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    sessions = [{"id": 0, "name": name}, {"id": 1, "name": "ArcadeBot 🤖"}]
    state = tic_tac_toe.create_state(sessions)

    while not tic_tac_toe.is_over(state):
        curr_id = tic_tac_toe.current_player(state)
        v = tic_tac_toe.view_for(state, 0)
        v["log"] = state.get("log", [])
        clear_screen()
        print(tic_tac_toe.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input(f"\n  ▶ YOUR TURN ({name}) — Choose position (1–9) or 'q' to quit: ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, cell_idx = tic_tac_toe.parse_action(state, 0, raw)
                if valid:
                    events = tic_tac_toe.apply_action(state, 0, cell_idx)
                    state["log"] = events.get("log", [])
                    break
                print(paint(f"  ! {cell_idx}", "1;31"))
        else:
            print("\n  🤖 ArcadeBot is making a move...")
            time.sleep(0.6)
            bot_cell = _get_best_ttt_cell(state["board"], "O", "X")
            events = tic_tac_toe.apply_action(state, 1, bot_cell)
            state["log"] = events.get("log", [])

    clear_screen()
    v = tic_tac_toe.view_for(state, 0)
    winners = tic_tac_toe.get_winner(state)
    msg = f"Winner: {', '.join(winners)}" if winners else "Draw!"
    print(tic_tac_toe.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Tic-Tac-Toe (vs Bot)", [name, "ArcadeBot 🤖"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 4. BATTLESHIP VS NAVAL AI
# ==========================================
def run_battleship_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("        BATTLESHIP — VS NAVAL AI", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Captain]: "), "Captain")

    sessions = [{"id": 0, "name": name}, {"id": 1, "name": "Naval AI ⚓"}]
    state = battleship.create_state(sessions)
    bot_targets_tried = set()

    while not battleship.is_over(state):
        curr_id = battleship.current_player(state)
        v = battleship.view_for(state, 0)
        v["log"] = state.get("log", [])
        clear_screen()
        print(battleship.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input(f"\n  ▶ YOUR RADAR TURN ({name}) — Target (e.g. C3, A1) or 'q' to quit: ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, coord = battleship.parse_action(v, 0, raw)
                if valid:
                    events = battleship.apply_action(state, 0, coord)
                    state["log"] = events.get("log", [])
                    break
                print(paint(f"  ! {coord}", "1;31"))
        else:
            print("\n  ⚓ Naval AI is calibrating torpedo trajectory...")
            time.sleep(0.8)
            # Pick random untargeted cell
            available = [(r, c) for r in range(5) for c in range(5) if (r, c) not in bot_targets_tried]
            bot_coord = random.choice(available)
            bot_targets_tried.add(bot_coord)
            events = battleship.apply_action(state, 1, bot_coord)
            state["log"] = events.get("log", [])

    clear_screen()
    v = battleship.view_for(state, 0)
    winners = battleship.get_winner(state)
    msg = f"Fleet Victor: {', '.join(winners)}" if winners else "Draw!"
    print(battleship.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Battleship (vs AI)", [name, "Naval AI ⚓"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 5. SNAKE & LADDERS VS BOTS
# ==========================================
def run_snake_and_ladder_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("     SNAKE & LADDERS — VS COMPUTER BOTS", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    bot_cnt = 1
    try:
        raw_cnt = input("How many bot opponents? (1–3) [1]: ").strip()
        if raw_cnt in {"1", "2", "3"}:
            bot_cnt = int(raw_cnt)
    except Exception:
        pass

    bot_names = ["Bot Nova 🤖", "Bot Pixel 👾", "Bot Turbo ⚡"]
    sessions = [{"id": 0, "name": name}]
    for i in range(bot_cnt):
        sessions.append({"id": i + 1, "name": bot_names[i]})

    state = snake_and_ladder.create_state(sessions)

    while not snake_and_ladder.is_over(state):
        curr_id = snake_and_ladder.current_player(state)
        v = snake_and_ladder.view_for(state, 0)
        clear_screen()
        print(snake_and_ladder.render_dashboard(v))

        curr_p = next(p for p in state["players"] if p["id"] == curr_id)

        if curr_id == 0:
            play_sound("turn")
            raw = input(f"\n  ▶ YOUR TURN ({name}) — Press [ENTER] to roll die (or 'q' to quit): ").strip()
            if raw.lower() in {"q", "quit", "exit"}:
                return
            snake_and_ladder.apply_action(state, 0, "roll")
        else:
            print(f"\n  🎲 {curr_p['name']} is shaking the dice cup...")
            time.sleep(0.7)
            snake_and_ladder.apply_action(state, curr_id, "roll")

    clear_screen()
    v = snake_and_ladder.view_for(state, 0)
    winners = snake_and_ladder.get_winner(state)
    msg = f"Champion: {', '.join(winners)}"
    print(snake_and_ladder.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Snake & Ladders (vs Bots)", [p["name"] for p in state["players"]], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 6. WORD CHAIN (SHIRITORI) VS LEXICON BOT
# ==========================================
def run_shiritori_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("     WORD CHAIN — VS LEXICON BOT", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    sessions = [{"id": 0, "name": name}, {"id": 1, "name": "LexiconBot 📚"}]
    state = shiritori.create_state(sessions)
    words_pool = list(get_words_set())

    while not shiritori.is_over(state):
        curr_id = shiritori.current_player(state)
        v = shiritori.view_for(state, 0)
        clear_screen()
        print(shiritori.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                req = state["required_letter"]
                prompt = f"\n  ▶ YOUR TURN ({name}) — Word starting with '{req}' (or 'pass', 'q' to quit): " if req else f"\n  ▶ YOUR TURN ({name}) — Enter starting word (or 'q' to quit): "
                raw = input(prompt).strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, word = shiritori.parse_action(state, 0, raw)
                if valid:
                    shiritori.apply_action(state, 0, word)
                    break
                print(paint(f"  ! {word}", "1;31"))
        else:
            print("\n  📚 LexiconBot is searching its vocabulary...")
            time.sleep(0.8)
            req = state["required_letter"]
            used = state["used_words"]
            # Find a word starting with req that hasn't been used
            matches = [w for w in words_pool if w.startswith(req) and w not in used and 3 <= len(w) <= 8] if req else [w for w in words_pool if 3 <= len(w) <= 6]
            if matches:
                bot_word = random.choice(matches[:50])
                shiritori.apply_action(state, 1, bot_word)
            else:
                shiritori.apply_action(state, 1, "PASS")

    clear_screen()
    v = shiritori.view_for(state, 0)
    winners = shiritori.get_winner(state)
    msg = f"Last Player Standing: {', '.join(winners)}" if winners else "Draw!"
    print(shiritori.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Word Chain (vs Bot)", [name, "LexiconBot 📚"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 7. SOLO WORDLE PRACTICE
# ==========================================
def run_solo_wordle():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("           SOLO WORDLE CHALLENGE", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    state = wordle.create_state([{"id": 0, "name": name}, {"id": 1, "name": "Solo Bot"}])

    while not wordle.is_over(state):
        clear_screen()
        v = wordle.view_for(state, 0)
        print(wordle.render_dashboard(v))

        play_sound("turn")
        raw = input("\n  ▶ Enter 5-letter word (or 'q' to quit): ").strip()
        if raw.lower() in {"q", "quit", "exit"}:
            return

        valid, word = wordle.parse_action(state, 0, raw)
        if valid:
            wordle.apply_action(state, 0, word)
        else:
            print(paint(f"  ! {word}", "1;31"))
            time.sleep(1.2)

    clear_screen()
    v = wordle.view_for(state, 0)
    winners = wordle.get_winner(state)
    target = state["target_word"]
    if state["solved"].get(0, False):
        msg = f"🎉 Congratulations {name}! You cracked the word '{target}'!"
        play_sound("win")
        tries = len(state["guesses"].get(0, []))
        record_high_score("wordle", name, 7 - tries, f"Solved in {tries} tries")
    else:
        msg = f"💀 Out of attempts! The secret word was '{target}'."
    print(wordle.render_final(v, msg, winners))
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 8. SOLO TRIVIA QUIZ CHALLENGE
# ==========================================
def run_solo_quiz_show():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("         SOLO COLLEGE TRIVIA QUIZ", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    state = quiz_show.create_state([{"id": 0, "name": name}, {"id": 1, "name": "QuizBot"}])

    while not quiz_show.is_over(state):
        clear_screen()
        v = quiz_show.view_for(state, 0)
        print(quiz_show.render_dashboard(v))

        play_sound("turn")
        raw = input("\n  ▶ Your Answer (A, B, C, D or 'q' to quit): ").strip()
        if raw.lower() in {"q", "quit", "exit"}:
            return

        valid, choice = quiz_show.parse_action(state, 0, raw)
        if valid:
            quiz_show.apply_action(state, 0, choice)
            # Advance bot answer automatically
            if not quiz_show.is_over(state):
                bot_choice = random.choice(["A", "B", "C", "D"])
                quiz_show.apply_action(state, 1, bot_choice)
        else:
            print(paint(f"  ! {choice}", "1;31"))
            time.sleep(1.0)

    clear_screen()
    v = quiz_show.view_for(state, 0)
    winners = quiz_show.get_winner(state)
    my_sc = state["scores"].get(0, 0)
    msg = f"Quiz Finished! Your Final Score: {my_sc} points."
    print(quiz_show.render_final(v, msg, winners))
    play_sound("win")
    record_high_score("quiz_show", name, my_sc, f"{my_sc} pts")
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 9. SOLO TYPING RACER VS SPEEDY BOT
# ==========================================
def run_solo_typing_racer():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("       TYPING RACER VS SPEEDY BOT 🏎️", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    state = typing_racer.create_state([{"id": 0, "name": name}, {"id": 1, "name": "SpeedyBot 🏎️"}])

    while not typing_racer.is_over(state):
        curr_id = typing_racer.current_player(state)
        clear_screen()
        v = typing_racer.view_for(state, 0)
        print(typing_racer.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            raw = input("\n  ▶ Type snippet above (or 'q' to quit): ").strip()
            if raw.lower() in {"q", "quit", "exit"}:
                return
            typing_racer.apply_action(state, 0, raw)
        else:
            time.sleep(0.5)
            # Bot types snippet with minor realistic delay/accuracy
            snip = typing_racer.TARGET_SNIPPETS[state.get("snippet_index", 0) % len(typing_racer.TARGET_SNIPPETS)]
            typing_racer.apply_action(state, 1, snip)

    clear_screen()
    v = typing_racer.view_for(state, 0)
    winners = typing_racer.get_winner(state)
    msg = f"Grand Prix Winner: {', '.join(winners)}!"
    print(typing_racer.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Typing Racer (vs Bot)", [name, "SpeedyBot 🏎️"], winners)
    input("\nPress Enter to return to solo menu...")

