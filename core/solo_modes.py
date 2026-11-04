"""
Solo and Offline Practice Modes for College LAN Arcade.
Allows single players to enjoy games against intelligent bots or in high-score chase mode.
"""
import copy
import math
import random
import time
from collections import deque
from config import clear_screen, paint, play_sound
from games import (
    connect4, tic_tac_toe, battleship, snake_and_ladder, game2048, shiritori,
    wordle, quiz_show, typing_racer, artillery, snake_duel, chess_game, arrow_man
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
WORDLE_STARTERS = ["CRANE", "SLATE", "STARE", "HEART", "OCEAN", "PLANT", "AUDIO", "ROAST", "SHINE"]
WORDLE_HUMAN_EXPLORERS = ["PILOT", "SHINE", "GHOST", "CLOUD", "STORM", "BREAD", "MUSIC", "WATER", "FLAME", "NIGHT"]


def _get_best_wordle_guess(state, bot_id=1, human_like=False):
    """
    Deduce next guess based on prior feedback.
    In human_like mode, simulates a human player's gradual exploration:
    never cheats to instantly solve on attempt 2, exploring vowels and consonants first.
    """
    guesses = state["guesses"].get(bot_id, [])
    target = state.get("target_word", "")
    candidates = list(wordle.TARGET_WORDS)

    if not guesses:
        for s in WORDLE_STARTERS:
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

    if not human_like:
        return random.choice(candidates)

    # Human-like pacing across 6 attempts
    attempt_num = len(guesses) + 1
    prior_words = ["".join(l for l, _ in g) for g in guesses]

    # Attempt 2: Human does NOT magically nail the secret word on turn 2
    if attempt_num == 2:
        non_target = [c for c in candidates if c != target and c not in prior_words]
        if non_target:
            return random.choice(non_target)
        for exp in WORDLE_HUMAN_EXPLORERS:
            if exp not in prior_words:
                return exp
        return random.choice(candidates)

    # Attempt 3: ~30% chance to pick target if known, else explore plausible candidate
    if attempt_num == 3:
        if target in candidates and len(candidates) > 1 and random.random() > 0.30:
            non_target = [c for c in candidates if c != target and c not in prior_words]
            if non_target:
                return random.choice(non_target)
        return random.choice(candidates)

    # Attempt 4: ~65% chance to solve
    if attempt_num == 4:
        if target in candidates and len(candidates) > 1 and random.random() > 0.65:
            non_target = [c for c in candidates if c != target and c not in prior_words]
            if non_target:
                return random.choice(non_target)
        return random.choice(candidates)

    # Attempt 5+: High solve rate (~90%)
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
            attempt_num = len(state["guesses"].get(1, [])) + 1
            if attempt_num == 1:
                print("\n  🤖 WordleBot is choosing a human opening word...")
            elif attempt_num == 2:
                print("\n  🤖 WordleBot is exploring untested vowel and consonant patterns...")
            elif attempt_num == 3:
                print("\n  🤖 WordleBot is narrowing down candidate letter clues...")
            else:
                print("\n  🤖 WordleBot is synthesizing the remaining clues...")
            time.sleep(1.0)
            bot_word = _get_best_wordle_guess(state, 1, human_like=True)
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
            curr_q = state["questions"][state["current_round"]]
            cat = curr_q.get("category", "")
            cat_accuracy = {
                "💻 Computer Science": 0.62,
                "🐍 Python": 0.60,
                "🌐 Networking & Web": 0.55,
                "🐧 Linux & OS": 0.55,
                "🎮 Gaming & Culture": 0.55,
                "🚀 Tech & Hardware": 0.50,
                "🧠 AI & Data": 0.50,
                "🌍 General Knowledge": 0.45,
                "🌍 Science": 0.45,
            }
            base_acc = cat_accuracy.get(cat, 0.52)
            # Pressure / streak regulation: human error increases if on a hot streak
            bot_streak = state["streaks"].get(1, 0)
            if bot_streak >= 1:
                base_acc = max(0.35, base_acc - 0.12 * bot_streak)

            deliberations = [
                "🤖 QuizBot is contemplating the question and weighing the options...",
                "🤖 QuizBot thinks it remembers this concept from college lecture...",
                "🤖 QuizBot eliminated two unlikely options and is taking an educated guess...",
                "🤖 QuizBot is debating between two plausible choices..."
            ]
            print(f"\n  {random.choice(deliberations)}")
            time.sleep(random.uniform(1.0, 1.4))

            correct_ans = curr_q["answer"]
            if random.random() < base_acc:
                bot_choice = correct_ans
            else:
                # Human-like mistake: pick a believable wrong answer among the remaining
                wrong_choices = [c for c in ["A", "B", "C", "D"] if c != correct_ans]
                bot_choice = random.choice(wrong_choices)
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
TYPO_MAP = {
    'a': 's', 'b': 'v', 'c': 'v', 'd': 'f', 'e': 'r', 'f': 'g', 'g': 'h',
    'h': 'j', 'i': 'o', 'j': 'k', 'k': 'l', 'l': 'k', 'm': 'n', 'n': 'm',
    'o': 'p', 'p': 'o', 'q': 'w', 'r': 't', 's': 'd', 't': 'y', 'u': 'i',
    'v': 'b', 'w': 'e', 'x': 'c', 'y': 'u', 'z': 'x',
    'A': 'S', 'B': 'V', 'C': 'V', 'D': 'F', 'E': 'R', 'F': 'G', 'G': 'H',
    'H': 'J', 'I': 'O', 'J': 'K', 'K': 'L', 'L': 'K', 'M': 'N', 'N': 'M',
    'O': 'P', 'P': 'O', 'Q': 'W', 'R': 'T', 'S': 'D', 'T': 'Y', 'U': 'I',
    'V': 'B', 'W': 'E', 'X': 'C', 'Y': 'U', 'Z': 'X'
}

def _make_human_typing_attempt(snip):
    """
    Generate realistic human typing output for SpeedyBot.
    Humans type around 55-70 WPM, occasionally making realistic typos,
    backspacing, or slipping on punctuation.
    """
    roll = random.random()

    # ~40% Clean typing (+35% Nitro boost, acc >= 90%)
    if roll < 0.40:
        return snip, "🏎️ SpeedyBot locked into a clean, rhythmic typing flow at ~70 WPM!"

    # ~45% Human typo / slight mistake (+20% forward move, acc ~75-85%)
    elif roll < 0.85:
        chars = list(snip)
        L = len(chars)
        k = max(2, int(round(L * 0.22)))
        step = max(2, L // k)
        for i in range(k):
            idx = min(L - 1, i * step + 1)
            c = chars[idx]
            chars[idx] = TYPO_MAP.get(c, 'x' if c != 'x' else 'z')
        res = "".join(chars)
        return res, "🏎️ SpeedyBot had slight typos on a few characters (+20% pace)!"

    # ~15% Stumble / fumble (+5% stumble, acc < 60%)
    else:
        half_len = max(3, len(snip) // 2)
        res = snip[:half_len]
        return res, "🏎️ SpeedyBot fumbled a word and had to backspace (+5% stumble)!"


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
            snip = typing_racer.get_current_snippet(state)
            bot_typed, msg = _make_human_typing_attempt(snip)
            print(f"\n  {msg}")
            time.sleep(random.uniform(1.1, 1.4))
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
def _get_best_artillery_shot(terrain, bot_x, target_x, wind, shot_num=1, human_like=False):
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

    if not human_like:
        jitter_ang = round(best_shot[0] + random.uniform(-3, 3), 1)
        jitter_pow = round(best_shot[1] + random.uniform(-4, 4), 1)
        jitter_ang = max(95.0, min(175.0, jitter_ang))
        jitter_pow = max(10.0, min(100.0, jitter_pow))
        return {"angle": jitter_ang, "power": jitter_pow}

    # Human Gunner Phased Ballistics:
    # Humans never have a built-in trajectory solver; they shoot, observe crater, and adjust.
    # Shot 1: Sighting / ranging shot (offset by ~12-16 tiles, 0 dmg).
    if shot_num == 1:
        p_offset = random.choice([-16.0, -14.0, 14.0])
        a_offset = random.uniform(-5.0, 5.0)
        h_ang = round(best_shot[0] + a_offset, 1)
        h_pow = round(best_shot[1] + p_offset, 1)
    # Shot 2: Bracketing shot (offset by ~5-8 tiles, at most splash 25 dmg, never direct kill).
    elif shot_num == 2:
        p_offset = random.choice([-8.0, -6.0, 7.0])
        a_offset = random.uniform(-3.0, 3.0)
        h_ang = round(best_shot[0] + a_offset, 1)
        h_pow = round(best_shot[1] + p_offset, 1)
    # Shot 3: Fine-tuning elevation & wind deflection (~2-4 tiles offset).
    elif shot_num == 3:
        p_offset = random.choice([-4.0, -2.0, 3.0])
        a_offset = random.uniform(-2.0, 2.0)
        h_ang = round(best_shot[0] + a_offset, 1)
        h_pow = round(best_shot[1] + p_offset, 1)
    # Shot 4+: Dialed-in effect fire (near miss or direct hit).
    else:
        h_ang = round(best_shot[0] + random.uniform(-1.5, 1.5), 1)
        h_pow = round(best_shot[1] + random.uniform(-2.0, 2.0), 1)

    h_ang = max(95.0, min(175.0, h_ang))
    h_pow = max(10.0, min(100.0, h_pow))
    return {"angle": h_ang, "power": h_pow}


def run_artillery_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("       ARTILLERY DUEL VS BALLISTICS AI 🎯", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Gunner]: "), "Gunner")

    state = artillery.create_state([{"id": 0, "name": name}, {"id": 1, "name": "Ballistics AI 🎯"}])
    bot_shot_count = 0

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
            bot_shot_count += 1
            if bot_shot_count == 1:
                print("\n  🎯 Ballistics AI is estimating distance and taking a ranging sighting shot...")
            elif bot_shot_count == 2:
                print("\n  🎯 Ballistics AI observed the first crater and is bracketing its angle...")
            elif bot_shot_count == 3:
                print("\n  🎯 Ballistics AI is fine-tuning elevation & wind compensation...")
            else:
                print("\n  🎯 Ballistics AI has dialed in range and fires for effect!")
            time.sleep(1.0)
            bot_x = state["positions"][1]
            target_x = state["positions"][0]
            wind = state["wind"]
            terrain = state["terrain"]
            bot_shot = _get_best_artillery_shot(terrain, bot_x, target_x, wind, shot_num=bot_shot_count, human_like=True)
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
def _get_best_snake_duel_move(state, bot_id=1, human_like=False):
    curr_x, curr_y = state["positions"][bot_id]
    dx, dy = state["directions"][bot_id]
    pellet = tuple(state["pellet"]) if state.get("pellet") else None

    all_trails = set(state["trails"].get(0, [])) | set(state["trails"].get(1, []))
    opp_pos = state["positions"].get(0)
    if opp_pos:
        all_trails.add(opp_pos)

    # 1. Immediate legal moves (avoid walls, solid bodies, and instant 180° reversals)
    candidates = {}
    for cmd, (ndx, ndy) in [("W", (0, -1)), ("S", (0, 1)), ("A", (-1, 0)), ("D", (1, 0))]:
        if (ndx, ndy) == (-dx, -dy) and len(state["trails"].get(bot_id, [])) > 1:
            continue
        nx = curr_x + ndx
        ny = curr_y + ndy
        if 0 <= nx < snake_duel.ARENA_WIDTH and 0 <= ny < snake_duel.ARENA_HEIGHT:
            if (nx, ny) not in all_trails:
                candidates[cmd] = (nx, ny, ndx, ndy)

    if not candidates:
        return "STRAIGHT"

    # Helper: Count accessible open space ahead using BFS flood-fill
    def count_open_space(start_pt):
        visited = set(all_trails)
        visited.add(start_pt)
        q = deque([start_pt])
        cnt = 0
        while q and cnt < 25:
            cx, cy = q.popleft()
            cnt += 1
            for qdx, qdy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                qx, qy = cx + qdx, cy + qdy
                if 0 <= qx < snake_duel.ARENA_WIDTH and 0 <= qy < snake_duel.ARENA_HEIGHT:
                    if (qx, qy) not in visited:
                        visited.add((qx, qy))
                        q.append((qx, qy))
        return cnt

    # 2. Direct BFS Shortest Path to Apple (Pellet)
    if pellet:
        queue = deque([((curr_x, curr_y), [])])
        visited = set(all_trails)
        visited.add((curr_x, curr_y))
        target_path = None
        while queue:
            (cx, cy), path = queue.popleft()
            if (cx, cy) == pellet:
                target_path = path
                break
            for cmd, (ndx, ndy) in [("W", (0, -1)), ("S", (0, 1)), ("A", (-1, 0)), ("D", (1, 0))]:
                if not path and (ndx, ndy) == (-dx, -dy) and len(state["trails"].get(bot_id, [])) > 1:
                    continue
                nx, ny = cx + ndx, cy + ndy
                if 0 <= nx < snake_duel.ARENA_WIDTH and 0 <= ny < snake_duel.ARENA_HEIGHT:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [cmd]))

        if target_path:
            first_cmd = target_path[0]
            if first_cmd in candidates:
                nxt_x, nxt_y, _, _ = candidates[first_cmd]
                # Follow the path to the apple if it leaves sufficient room to escape (no suicide coils)
                my_len = len(state["trails"].get(bot_id, []))
                if count_open_space((nxt_x, nxt_y)) >= min(6, my_len + 1):
                    return first_cmd

    # 3. Fallback: Score candidate moves combining open space, fruit attraction, and forward momentum
    scored = []
    for cmd, (nx, ny, ndx, ndy) in candidates.items():
        space = count_open_space((nx, ny))
        score = space * 3.5

        if pellet:
            dist = abs(nx - pellet[0]) + abs(ny - pellet[1])
            # Consistent global attraction to apple across the entire arena
            score += max(0, 50 - dist * 2.5)

        # Slight forward momentum preference when open
        if (ndx, ndy) == (dx, dy):
            score += 2.0

        if human_like:
            score += random.uniform(-0.5, 0.5)

        scored.append((score, cmd))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


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
            bot_cmd = _get_best_snake_duel_move(state, 1, human_like=True)
            snake_duel.apply_action(state, 1, bot_cmd)

    clear_screen()
    v = snake_duel.view_for(state, 0)
    winners = snake_duel.get_winner(state)
    my_sc = state.get("scores", {}).get(0, 0)
    bot_sc = state.get("scores", {}).get(1, 0)
    my_len = state.get("lengths", {}).get(0, 2)

    if winners and winners[0] == name:
        msg = f"🏆 VICTORY! TronBot crashed! {name} survives with {my_sc} pts (Length: {my_len})!"
        play_sound("win")
        record_high_score("snake_duel", name, my_sc, f"{my_sc} pts (Length: {my_len})")
    elif winners and "TronBot" in winners[0]:
        msg = f"💥 You crashed! TronBot wins the duel ({my_sc} vs {bot_sc} pts)!"
    else:
        msg = f"Arena tie! (Final score: You {my_sc} - {bot_sc} TronBot)"

    print(snake_duel.render_final(v, msg, winners))
    record_match_outcome("Snake Duel (vs Bot)", [name, "TronBot ⚡"], winners)
    input("\nPress Enter to return to solo menu...")


# ==========================================
# 12. CHESS VS CHESS BOT
# ==========================================
# Standard human opening responses for Black (Rank 8 is row 0, Rank 7 is row 1)
BLACK_OPENING_BOOK = {
    # After White 1. e4
    "e2e4": [
        ((1, 4), (3, 4)),  # 1... e5 (King's Pawn)
        ((1, 2), (3, 2)),  # 1... c5 (Sicilian)
        ((1, 4), (2, 4)),  # 1... e6 (French)
    ],
    # After White 1. d4
    "d2d4": [
        ((1, 3), (3, 3)),  # 1... d5
        ((0, 6), (2, 5)),  # 1... Nf6 (Indian)
    ],
    # After 1. e4 e5 2. Nf3
    "e2e4_e7e5_g1f3": [
        ((0, 1), (2, 2)),  # 2... Nc6 (classic defense of e5)
        ((0, 6), (2, 5)),  # 2... Nf6 (Petrov defense)
    ],
    # After 1. e4 e5 2. Bc4
    "e2e4_e7e5_f1c4": [
        ((0, 6), (2, 5)),  # 2... Nf6
        ((0, 1), (2, 2)),  # 2... Nc6
    ],
    # After 1. e4 e5 2. Qh5 (Wayward Queen attack)
    "e2e4_e7e5_d1h5": [
        ((0, 1), (2, 2)),  # 2... Nc6 (defend e5!)
    ],
    # After 1. d4 d5 2. c4 (Queen's Gambit)
    "d2d4_d7d5_c2c4": [
        ((1, 4), (2, 4)),  # 2... e6 (QGD)
        ((1, 2), (2, 2)),  # 2... c6 (Slav)
    ]
}


def _get_best_chess_move(board, moves_history=None, human_like=False):
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

    if not human_like:
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

    # Human-like Chess Playing:
    # 1. Opening Book matching
    if moves_history:
        clean_moves = []
        for mh in moves_history:
            parts = mh.split("➔")
            if len(parts) == 2:
                from_c = parts[0][-2:].strip().lower()
                to_c = parts[1][:2].strip().lower()
                clean_moves.append(f"{from_c}{to_c}")

        key = "_".join(clean_moves)
        if key in BLACK_OPENING_BOOK:
            book_choices = [mv for mv in BLACK_OPENING_BOOK[key] if mv in legal_moves]
            if book_choices:
                choice = random.choice(book_choices)
                (r1, c1), (r2, c2) = choice
                return {"from": (r1, c1), "to": (r2, c2), "notation": f"{chess_game.to_coord(r1, c1)}{chess_game.to_coord(r2, c2)}"}

    # 2. Human Heuristic Evaluation (Piece development, center, king safety, defended pieces)
    scored = []
    for (r1, c1), (r2, c2) in legal_moves:
        p = board[r1][c1]
        target = board[r2][c2]
        score = 0.0

        # Material gain
        if target is not None:
            score += piece_vals.get(target, 1) * 10.0

        # Center control (d5, e5, d4, e4)
        if 2 <= r2 <= 5 and 2 <= c2 <= 5:
            score += 1.5

        # Minor piece development (knights and bishops off back rank)
        if p in {"n", "b"} and r1 == 0 and r2 > 0:
            score += 3.0

        # King safety: avoid moving King out into the open early
        if p == "k" and r1 == 0 and r2 != 0:
            score -= 4.0

        # Don't move Queen too early without good target
        if p == "q" and target is None and len(moves_history or []) < 6:
            score -= 2.0

        # Guarded square penalty (avoid moving valuable piece into a square attacked by White)
        tb = copy.deepcopy(board)
        tb[r2][c2] = tb[r1][c1]
        tb[r1][c1] = None
        is_attacked = False
        for wr in range(8):
            for wc in range(8):
                wp = tb[wr][wc]
                if wp and chess_game.is_white_piece(wp):
                    v, _ = chess_game.is_valid_piece_move(tb, wr, wc, r2, c2, True)
                    if v:
                        is_attacked = True
                        break
            if is_attacked:
                break

        if is_attacked:
            my_val = piece_vals.get(p, 1)
            target_val = piece_vals.get(target, 0) if target else 0
            if my_val > target_val:
                score -= (my_val - target_val) * 7.0

        # Check bonus
        if chess_game.is_king_in_check(tb, True):
            score += 3.5

        score += random.uniform(-0.5, 0.5)
        scored.append((score, ((r1, c1), (r2, c2))))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score = scored[0][0]
    top_candidates = [m for sc, m in scored if sc >= best_score - 1.0]
    choice = random.choice(top_candidates)
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
            turn_cnt = len(state.get("moves_history", []))
            if turn_cnt <= 2:
                print("\n  ♟️ ChessBot is developing its pieces according to classical opening principles...")
            else:
                print("\n  ♟️ ChessBot is evaluating tactical positioning and piece safety...")
            time.sleep(1.0)
            bot_move = _get_best_chess_move(state["board"], state.get("moves_history", []), human_like=True)
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


# ==========================================
# 14. ARROW MAN DUEL VS ROBIN BOT
# ==========================================
def _get_best_arrow_man_shot(state, bot_id=1, shot_num=1, human_like=True):
    p1_x = state["positions"][state["players"][0]["id"]]
    p2_x = state["positions"][state["players"][1]["id"]]
    t1_top = state.get("tower_tops", {}).get(state["players"][0]["id"], 10)
    t2_top = state.get("tower_tops", {}).get(state["players"][1]["id"], 10)
    wind = state.get("wind", 0)
    opp_apple = state.get("apples", {}).get(state["players"][0]["id"], True)
    quiv = state.get("quivers", {}).get(bot_id, {})

    arrow_choice = "standard"
    if quiv.get("bomb", 0) > 0 and shot_num >= 3:
        arrow_choice = "bomb"
    elif quiv.get("fire", 0) > 0 and shot_num >= 2 and random.random() < 0.6:
        arrow_choice = "fire"
    elif quiv.get("pierce", 0) > 0 and abs(wind) >= 3:
        arrow_choice = "pierce"

    best_candidate = None
    min_dist = 999.0

    target_y = float(arrow_man.ARENA_HEIGHT - 1 - t1_top + 2)

    for test_ang in range(35, 65, 3):
        for test_pow in range(40, 95, 2):
            _, hit_type, dmg, impact, apple_hit = arrow_man.simulate_arrow_flight(
                p1_x, p2_x, 1, test_ang, test_pow, wind, arrow_choice, opp_apple, t1_top, t2_top
            )
            ix, iy = impact
            dist = abs(ix - p1_x) + abs(iy - target_y)
            if hit_type in {"apple", "head", "body"}:
                best_candidate = (test_ang, test_pow)
                break
            if dist < min_dist:
                min_dist = dist
                best_candidate = (test_ang, test_pow)
        if best_candidate and hit_type in {"apple", "head"}:
            break

    if not best_candidate:
        best_candidate = (45, 68)

    if not human_like:
        return {"angle": best_candidate[0], "power": best_candidate[1], "arrow": arrow_choice}

    if shot_num == 1:
        p_offset = random.choice([-12.0, -10.0, 10.0])
        a_offset = random.uniform(-4.0, 4.0)
    elif shot_num == 2:
        p_offset = random.choice([-6.0, 5.0, -4.0])
        a_offset = random.uniform(-2.5, 2.5)
    elif shot_num == 3:
        p_offset = random.choice([-3.0, 3.0, 0.0])
        a_offset = random.uniform(-1.5, 1.5)
    else:
        p_offset = random.uniform(-1.5, 1.5)
        a_offset = random.uniform(-1.0, 1.0)

    final_ang = max(20.0, min(80.0, round(best_candidate[0] + a_offset, 1)))
    final_pow = max(20.0, min(95.0, round(best_candidate[1] + p_offset, 1)))
    return {"angle": final_ang, "power": final_pow, "arrow": arrow_choice}


def run_arrow_man_vs_ai():
    clear_screen()
    print(paint("=" * 50, "1;36"))
    print(paint("       ARROW MAN DUEL VS ROBIN BOT 🏹", "1;36"))
    print(paint("=" * 50, "1;36"))
    name = clean_name(input("\nEnter your player name [Archer]: "), "Archer")

    state = arrow_man.create_state([{"id": 0, "name": name}, {"id": 1, "name": "RobinBot 🏹"}])
    bot_shot_count = 0

    while not arrow_man.is_over(state):
        curr_id = arrow_man.current_player(state)
        clear_screen()
        v = arrow_man.view_for(state, 0)
        print(arrow_man.render_dashboard(v))

        if curr_id == 0:
            play_sound("turn")
            while True:
                raw = input("\n  ▶ Enter Angle & Power (e.g. '45 70' or '50 75 fire', 'q' to quit): ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    return
                valid, action_data = arrow_man.parse_action(state, 0, raw)
                if valid:
                    arrow_man.apply_action(state, 0, action_data)
                    break
                print(paint(f"  ! {action_data}", "1;31"))
        else:
            bot_shot_count += 1
            if bot_shot_count == 1:
                print("\n  🏹 RobinBot is notching an arrow and checking the crosswind...")
            elif bot_shot_count == 2:
                print("\n  🏹 RobinBot noticed the trajectory and is adjusting bow elevation...")
            elif bot_shot_count == 3:
                print("\n  🏹 RobinBot has calculated the distance and draws to full extension...")
            else:
                print("\n  🏹 RobinBot takes careful aim at your head and releases!")
            time.sleep(1.0)
            bot_shot = _get_best_arrow_man_shot(state, bot_id=1, shot_num=bot_shot_count, human_like=True)
            arrow_man.apply_action(state, 1, bot_shot)

    clear_screen()
    v = arrow_man.view_for(state, 0)
    winners = arrow_man.get_winner(state)
    my_hp = state["hp"].get(0, 0)
    if winners and winners[0] == name:
        msg = f"🏆 VICTORY! {name} defeated RobinBot with {my_hp} HP remaining!"
        play_sound("win")
        record_high_score("arrow_man", name, my_hp, f"{my_hp} HP left")
    elif winners and "RobinBot" in winners[0]:
        msg = "💀 DEFEAT! RobinBot felled you in battle!"
    else:
        msg = "Archery duel ended in a draw!"

    print(arrow_man.render_final(v, msg, winners))
    record_match_outcome("Arrow Man Duel (vs AI)", [name, "RobinBot 🏹"], winners)
    input("\nPress Enter to return to solo menu...")


