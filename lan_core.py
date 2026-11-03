#!/usr/bin/env python3
"""
COLLEGE LAN ARCADE
Terminal-based multiplayer LAN game platform for college networks.

Run:
  python3 lan_core.py
"""
import sys
import time
import config
from config import clear_screen, paint
from core.client import join_lan_game
from core.renderer import render_menu
from core.server import host_lan_game_session
from core.solo_modes import (
    run_solo_2048,
    run_connect4_vs_ai,
    run_battleship_vs_ai,
    run_tic_tac_toe_vs_ai,
    run_snake_and_ladder_vs_ai,
    run_shiritori_vs_ai,
    run_solo_wordle,
    run_solo_quiz_show,
    run_solo_typing_racer
)
from utils.stats import render_hall_of_fame
from games import (
    bingo, connect4, battleship,
    dots_and_boxes, tic_tac_toe, hangman,
    shiritori, game2048,
    boggle, mini_crossword, wordoku, scrabble_sprint, snake_and_ladder,
    chess_game, wordle, quiz_show, typing_racer
)


def host_menu():
    while True:
        clear_screen()
        options = [
            f"Bingo ({bingo.min_players}–{bingo.max_players} players)",
            f"Connect Four ({connect4.min_players} players)",
            f"Battleship ({battleship.min_players} players)",
            f"Dots and Boxes ({dots_and_boxes.min_players}–{dots_and_boxes.max_players} players)",
            f"Tic-Tac-Toe ({tic_tac_toe.min_players} players)",
            f"Hangman ({hangman.min_players} players)",
            f"Word Chain / Shiritori ({shiritori.min_players}–{shiritori.max_players} players)",
            f"2048 Versus ({game2048.min_players} players)",
            f"Boggle / Word Hunt ({boggle.min_players}–{boggle.max_players} players)",
            f"Mini Crossword Race ({mini_crossword.min_players} players)",
            f"Wordoku Mini Sudoku ({wordoku.min_players} players)",
            f"Anagram Showdown ({scrabble_sprint.min_players}–{scrabble_sprint.max_players} players)",
            f"Snake & Ladders ({snake_and_ladder.min_players}–{snake_and_ladder.max_players} players)",
            f"Chess ({chess_game.min_players} players)",
            f"Wordle Versus ({wordle.min_players} players)",
            f"College Quiz Show ({quiz_show.min_players}–{quiz_show.max_players} players)",
            f"Typing Racer ({typing_racer.min_players}–{typing_racer.max_players} players)",
            "Back to Main Menu"
        ]
        print(render_menu("HOST A LAN GAME", options))
        choice = input("Select game option: ").strip()

        if choice == "1":
            host_lan_game_session(bingo)
            break
        elif choice == "2":
            host_lan_game_session(connect4)
            break
        elif choice == "3":
            host_lan_game_session(battleship)
            break
        elif choice == "4":
            host_lan_game_session(dots_and_boxes)
            break
        elif choice == "5":
            host_lan_game_session(tic_tac_toe)
            break
        elif choice == "6":
            host_lan_game_session(hangman)
            break
        elif choice == "7":
            host_lan_game_session(shiritori)
            break
        elif choice == "8":
            host_lan_game_session(game2048)
            break
        elif choice == "9":
            host_lan_game_session(boggle)
            break
        elif choice == "10":
            host_lan_game_session(mini_crossword)
            break
        elif choice == "11":
            host_lan_game_session(wordoku)
            break
        elif choice == "12":
            host_lan_game_session(scrabble_sprint)
            break
        elif choice == "13":
            host_lan_game_session(snake_and_ladder)
            break
        elif choice == "14":
            host_lan_game_session(chess_game)
            break
        elif choice == "15":
            host_lan_game_session(wordle)
            break
        elif choice == "16":
            host_lan_game_session(quiz_show)
            break
        elif choice == "17":
            host_lan_game_session(typing_racer)
            break
        elif choice == "18" or choice.lower() in {"q", "back", "exit"}:
            break
        else:
            print("Please enter 1–18.")
            input("Press Enter to continue...")


def solo_menu():
    while True:
        clear_screen()
        options = [
            "Bingo (vs Computer Bot)",
            "2048 (Solo Endless High-Score Chase)",
            "Connect Four (vs Minimax AI)",
            "Battleship (vs Tactical Hunt AI)",
            "Tic-Tac-Toe (vs Optimal AI)",
            "Snake & Ladders (vs Dice Bot)",
            "Word Chain / Shiritori (vs Lexicon Bot)",
            "Wordle (Solo 6-Attempt Challenge)",
            "College Quiz Show (Solo Trivia Challenge)",
            "Typing Racer (vs Speedy Bot 🏎️)",
            "Back to Main Menu"
        ]
        print(render_menu("SOLO & OFFLINE ARCADE", options))
        choice = input("Select solo game: ").strip()

        if choice == "1":
            bingo.solo_setup()
        elif choice == "2":
            run_solo_2048()
        elif choice == "3":
            run_connect4_vs_ai()
        elif choice == "4":
            run_battleship_vs_ai()
        elif choice == "5":
            run_tic_tac_toe_vs_ai()
        elif choice == "6":
            run_snake_and_ladder_vs_ai()
        elif choice == "7":
            run_shiritori_vs_ai()
        elif choice == "8":
            run_solo_wordle()
        elif choice == "9":
            run_solo_quiz_show()
        elif choice == "10":
            run_solo_typing_racer()
        elif choice == "11" or choice.lower() in {"q", "back", "exit"}:
            break
        else:
            print("Please enter 1–11.")
            input("Press Enter to continue...")


def main():
    while True:
        clear_screen()
        sound_status = paint("ON", "1;32") if config.SOUND_ENABLED else paint("OFF", "31")
        options = [
            "Host a LAN Game",
            "Join a LAN Game (Wi-Fi Auto-Discovery)",
            "Solo & Offline Arcade (Play vs Computer AI)",
            "Arcade Hall of Fame & Leaderboards",
            f"Toggle Audio Effects (Currently: {sound_status})",
            "Exit"
        ]
        print(render_menu("COLLEGE LAN ARCADE", options))
        choice = input("Select option: ").strip()

        if choice == "1":
            host_menu()
        elif choice == "2":
            join_lan_game()
        elif choice == "3":
            solo_menu()
        elif choice == "4":
            clear_screen()
            print(render_hall_of_fame())
            input("\nPress Enter to return to main menu...")
        elif choice == "5":
            config.SOUND_ENABLED = not config.SOUND_ENABLED
            st = "ENABLED 🔔" if config.SOUND_ENABLED else "MUTED 🔕"
            print(paint(f"\n  Audio cues {st}!", "1;33"))
            time.sleep(0.6)
        elif choice == "6":
            print("\nThanks for playing College LAN Arcade!")
            sys.exit(0)
        else:
            print("Please choose 1–6.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        if "--server" in sys.argv:
            from core.server import run_dedicated_server
            run_dedicated_server()
        else:
            main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nArcade closed. See you next time!")
        sys.exit(0)
