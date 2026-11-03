"""
Solo and Offline Practice Modes for College LAN Arcade.
Allows single players to enjoy games against intelligent bots or in high-score chase mode.
"""
import copy
import math
import random
import time
from config import clear_screen, paint, play_sound
from games import (
    connect4, tic_tac_toe, battleship, snake_and_ladder, game2048, shiritori,
    wordle, quiz_show, typing_racer, artillery, snake_duel, chess_game
)
from utils.input import read_direct_key
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
            used = {w.upper() for w in state["used_words"]}
            if req:
                req_up = req.upper()
                matches = [w for w in words_pool if w.upper().startswith(req_up) and w.upper() not in used and 3 <= len(w) <= 8]
            else:
                matches = [w for w in words_pool if 3 <= len(w) <= 6]
            if matches:
                bot_word = random.choice(matches[:50]).upper()
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
def _get_best_wordle_guess(state, bot_id=1):
    """Filter candidate target words against all prior green/yellow/gray feedback."""
    guesses = state["guesses"].get(bot_id, [])
    candidates = list(wordle.TARGET_WORDS)

    if not guesses:
        starters = ["CRANE", "SLATE", "STARE", "HEART", "OCEAN", "PLANT"]
        for s in starters:
            if s in candidates:
                return s
        return random.choice(candidates)

    for g_eval in guesses:
        guess_str = "".join(l for l, _ in g_eval)
        new_candidates = []
        for cand in candidates:
            if cand == guess_str:
                continue
            cand_eval = wordle.evaluate_guess(cand, guess_str)
            if [st for _, st in cand_eval] == [st for _, st in g_eval]:
                new_candidates.append(cand)
        if new_candidates:
            candidates = new_candidates

    return random.choice(candidates)


def run_solo_wordle():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("           SOLO WORDLE CHALLENGE", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Player]: "), "Player")

    state = wordle.create_state([{"id": 0, "name": name}, {"id": 1, "name": "WordleBot 🤖"}])

    while not wordle.is_over(state):
        curr_id = wordle.current_player(state)
        clear_screen()
        v = wordle.view_for(state, 0)
        print(wordle.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input("\n  ▶ YOUR TURN — Enter 5-letter word (or 'q' to quit): ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, word = wordle.parse_action(state, 0, raw)
                if valid:
                    wordle.apply_action(state, 0, word)
                    break
                print(paint(f"  ! {word}", "1;31"))
        else:
            print("\n  🤖 WordleBot is analyzing letter frequencies and clues...")
            time.sleep(1.0)
            bot_word = _get_best_wordle_guess(state, 1)
            wordle.apply_action(state, 1, bot_word)

    clear_screen()
    v = wordle.view_for(state, 0)
    winners = wordle.get_winner(state)
    target = state["target_word"]
    if state["solved"].get(0, False):
        tries = len(state["guesses"].get(0, []))
        msg = f"🎉 Congratulations {name}! You cracked '{target}' in {tries} tries!"
        play_sound("win")
        record_high_score("wordle", name, 7 - tries, f"Solved in {tries} tries")
    elif state["solved"].get(1, False):
        bot_tries = len(state["guesses"].get(1, []))
        msg = f"🤖 WordleBot cracked the word '{target}' in {bot_tries} tries! You were outsmarted!"
    else:
        msg = f"💀 Out of attempts! The secret word was '{target}'."
    print(wordle.render_final(v, msg, winners))
    record_match_outcome("Wordle (vs Bot)", [name, "WordleBot 🤖"], winners)
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

    state = quiz_show.create_state([{"id": 0, "name": name}, {"id": 1, "name": "QuizBot 🤖"}])

    while not quiz_show.is_over(state):
        curr_id = quiz_show.current_player(state)
        clear_screen()
        v = quiz_show.view_for(state, 0)
        print(quiz_show.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input("\n  ▶ YOUR TURN — Answer (A, B, C, D or 'q' to quit): ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, choice = quiz_show.parse_action(state, 0, raw)
                if valid:
                    quiz_show.apply_action(state, 0, choice)
                    break
                print(paint(f"  ! {choice}", "1;31"))
        else:
            print("\n  🤖 QuizBot is contemplating the question...")
            time.sleep(1.2)
            curr_q = state["questions"][state["current_round"]]
            if random.random() < 0.70:
                bot_choice = curr_q["answer"]
            else:
                bot_choice = random.choice(["A", "B", "C", "D"])
            quiz_show.apply_action(state, 1, bot_choice)

    clear_screen()
    v = quiz_show.view_for(state, 0)
    winners = quiz_show.get_winner(state)
    my_sc = state["scores"].get(0, 0)
    bot_sc = state["scores"].get(1, 0)
    msg = f"Quiz Finished! Your Final Score: {my_sc} pts | QuizBot: {bot_sc} pts."
    print(quiz_show.render_final(v, msg, winners))
    play_sound("win")
    record_high_score("quiz_show", name, my_sc, f"{my_sc} pts")
    record_match_outcome("Quiz Show (vs Bot)", [name, "QuizBot 🤖"], winners)
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
            print("\n  🏎️ SpeedyBot is typing furiously at 90 WPM...")
            time.sleep(1.0)
            snip = typing_racer.TARGET_SNIPPETS[state.get("snippet_index", 0) % len(typing_racer.TARGET_SNIPPETS)]
            if random.random() < 0.85:
                bot_typed = snip
            else:
                bot_typed = snip[:-1] + ("x" if snip[-1] != "x" else "y")
            typing_racer.apply_action(state, 1, bot_typed)

    clear_screen()
    v = typing_racer.view_for(state, 0)
    winners = typing_racer.get_winner(state)
    msg = f"Grand Prix Winner: {', '.join(winners)}!"
    print(typing_racer.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Typing Racer (vs Bot)", [name, "SpeedyBot 🏎️"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 10. ARTILLERY DUEL VS BALLISTICS AI
# ==========================================
def _get_best_artillery_shot(terrain, bot_x, target_x, wind):
    best_shot = (135.0, 60.0)
    best_dist = 999

    for test_angle in [120, 130, 135, 140, 150]:
        for test_power in range(35, 95, 5):
            pts, ix, iy, direct, dmg = artillery.simulate_ballistic_flight(
                terrain, bot_x, target_x, test_angle, test_power, wind
            )
            dist = abs(ix - target_x)
            if dist < best_dist:
                best_dist = dist
                best_shot = (float(test_angle), float(test_power))
            if dist == 0:
                break
        if best_dist == 0:
            break

    jitter_ang = round(best_shot[0] + random.uniform(-3, 3), 1)
    jitter_pow = round(best_shot[1] + random.uniform(-4, 4), 1)
    jitter_ang = max(95.0, min(175.0, jitter_ang))
    jitter_pow = max(10.0, min(100.0, jitter_pow))
    return {"angle": jitter_ang, "power": jitter_pow}


def run_artillery_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("       ARTILLERY DUEL VS BALLISTICS AI 🎯", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Gunner]: "), "Gunner")

    state = artillery.create_state([{"id": 0, "name": name}, {"id": 1, "name": "Ballistics AI 🎯"}])

    while not artillery.is_over(state):
        curr_id = artillery.current_player(state)
        clear_screen()
        v = artillery.view_for(state, 0)
        print(artillery.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input("\n  ▶ Enter Angle (0–180°) and Power (1–100) (e.g. '45 60' or 'q' to quit): ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, shot_data = artillery.parse_action(state, 0, raw)
                if valid:
                    artillery.apply_action(state, 0, shot_data)
                    break
                print(paint(f"  ! {shot_data}", "1;31"))
        else:
            print("\n  🎯 Ballistics AI is calculating wind deflection & ballistic arc...")
            time.sleep(1.0)
            bot_x = state["positions"][1]
            target_x = state["positions"][0]
            wind = state["wind"]
            terrain = state["terrain"]
            bot_shot = _get_best_artillery_shot(terrain, bot_x, target_x, wind)
            artillery.apply_action(state, 1, bot_shot)

    clear_screen()
    v = artillery.view_for(state, 0)
    winners = artillery.get_winner(state)
    msg = f"Victor: {', '.join(winners)}!" if winners else "Artillery Draw!"
    print(artillery.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Artillery Duel (vs AI)", [name, "Ballistics AI 🎯"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 11. SNAKE DUEL VS TRON BOT
# ==========================================
def _get_best_snake_duel_move(state, bot_id=1):
    curr_x, curr_y = state["positions"][bot_id]
    dx, dy = state["directions"][bot_id]
    pellet = state.get("pellet")

    all_trails = set(state["trails"].get(0, [])) | set(state["trails"].get(1, []))
    opp_pos = state["positions"].get(0)
    if opp_pos:
        all_trails.add(opp_pos)

    candidates = []
    for cmd, (ndx, ndy) in [("W", (0, -1)), ("S", (0, 1)), ("A", (-1, 0)), ("D", (1, 0))]:
        if (ndx, ndy) == (-dx, -dy) and len(state["trails"].get(bot_id, [])) > 1:
            continue
        nx = curr_x + ndx
        ny = curr_y + ndy
        if 0 <= nx < snake_duel.ARENA_WIDTH and 0 <= ny < snake_duel.ARENA_HEIGHT:
            if (nx, ny) not in all_trails:
                candidates.append((cmd, (nx, ny)))

    if not candidates:
        return "STRAIGHT"

    if pellet:
        candidates.sort(key=lambda item: abs(item[1][0] - pellet[0]) + abs(item[1][1] - pellet[1]))

    return candidates[0][0]


def run_snake_duel_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("         SNAKE DUEL VS TRON BOT ⚡", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Rider]: "), "Rider")

    state = snake_duel.create_state([{"id": 0, "name": name}, {"id": 1, "name": "TronBot ⚡"}])

    while not snake_duel.is_over(state):
        curr_id = snake_duel.current_player(state)
        clear_screen()
        v = snake_duel.view_for(state, 0)
        print(snake_duel.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            print(paint("\n  ▶ Steer: Arrow Keys or W/A/S/D (direct keypress, 'q' to quit):", "1;33"), end="", flush=True)
            cmd = read_direct_key()
            if cmd is None or cmd.lower() in {"q", "!ff"}:
                return
            valid, act = snake_duel.parse_action(state, 0, cmd)
            if valid:
                snake_duel.apply_action(state, 0, act)
            else:
                snake_duel.apply_action(state, 0, "STRAIGHT")
        else:
            time.sleep(0.4)
            bot_cmd = _get_best_snake_duel_move(state, 1)
            snake_duel.apply_action(state, 1, bot_cmd)

    clear_screen()
    v = snake_duel.view_for(state, 0)
    winners = snake_duel.get_winner(state)
    msg = f"Arena Champion: {', '.join(winners)}!" if winners else "Mutual Crash!"
    print(snake_duel.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Snake Duel (vs Bot)", [name, "TronBot ⚡"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 12. CHESS VS CHESS BOT
# ==========================================
def _get_best_chess_move(board):
    legal_moves = []
    for r1 in range(8):
        for c1 in range(8):
            p = board[r1][c1]
            if p is not None and chess_game.is_black_piece(p):
                for r2 in range(8):
                    for c2 in range(8):
                        valid, err = chess_game.is_valid_piece_move(board, r1, c1, r2, c2, False)
                        if valid:
                            tb = copy.deepcopy(board)
                            tb[r2][c2] = tb[r1][c1]
                            tb[r1][c1] = None
                            if not chess_game.is_king_in_check(tb, False):
                                legal_moves.append(((r1, c1), (r2, c2)))
    if not legal_moves:
        return None

    piece_vals = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100,
                  "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100}
    scored = []
    for (r1, c1), (r2, c2) in legal_moves:
        target = board[r2][c2]
        score = 0
        if target is not None:
            score += piece_vals.get(target, 1) * 10
        if 2 <= r2 <= 5 and 2 <= c2 <= 5:
            score += 1
        scored.append((score, ((r1, c1), (r2, c2))))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score = scored[0][0]
    best_candidates = [m for sc, m in scored if sc == best_score]
    choice = random.choice(best_candidates)
    (r1, c1), (r2, c2) = choice
    from_str = chess_game.to_coord(r1, c1)
    to_str = chess_game.to_coord(r2, c2)
    return {"from": (r1, c1), "to": (r2, c2), "notation": f"{from_str}{to_str}"}


def run_chess_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("           CHESS VS CHESS BOT ♟️", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Grandmaster]: "), "Grandmaster")

    state = chess_game.create_state([{"id": 0, "name": name}, {"id": 1, "name": "ChessBot ♟️"}])

    while not chess_game.is_over(state):
        curr_id = chess_game.current_player(state)
        clear_screen()
        v = chess_game.view_for(state, 0)
        print(chess_game.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input("\n  ▶ YOUR TURN (White) — Move (e.g. 'e2e4' or 'e2 e4', 'q' to quit): ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, move_data = chess_game.parse_action(state, 0, raw)
                if valid:
                    chess_game.apply_action(state, 0, move_data)
                    break
                print(paint(f"  ! {move_data}", "1;31"))
        else:
            print("\n  ♟️ ChessBot is calculating positional strategy...")
            time.sleep(1.0)
            bot_move = _get_best_chess_move(state["board"])
            if bot_move:
                chess_game.apply_action(state, 1, bot_move)
            else:
                # Checkmate / Stalemate
                break

    clear_screen()
    v = chess_game.view_for(state, 0)
    winners = chess_game.get_winner(state)
    msg = f"Checkmate! Winner: {', '.join(winners)}!" if winners else "Game Drawn / Concluded."
    print(chess_game.render_final(v, msg, winners))
    play_sound("win")
    record_match_outcome("Chess (vs Bot)", [name, "ChessBot ♟️"], winners)
    input("\nPress Enter to return to solo menu...")


