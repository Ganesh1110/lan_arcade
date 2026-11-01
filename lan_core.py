#!/usr/bin/env python3
"""
COLLEGE LAN ARCADE
Terminal-based multiplayer LAN game platform for college networks.

Run:
  python3 lan_core.py
"""
import sys
from config import clear_screen, paint
from core.client import join_lan_game
from core.renderer import render_menu
from core.server import host_lan_game_session
from games import (
    bingo, connect4, battleship,
    dots_and_boxes, tic_tac_toe, hangman, rock_paper_scissors,
    shiritori, game2048, number_duel
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
            f"Rock, Paper, Scissors ({rock_paper_scissors.min_players} players)",
            f"Word Chain / Shiritori ({shiritori.min_players}–{shiritori.max_players} players)",
            f"2048 Versus ({game2048.min_players} players)",
            f"Number Duel High-Low ({number_duel.min_players}–{number_duel.max_players} players)",
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
            host_lan_game_session(rock_paper_scissors)
            break
        elif choice == "8":
            host_lan_game_session(shiritori)
            break
        elif choice == "9":
            host_lan_game_session(game2048)
            break
        elif choice == "10":
            host_lan_game_session(number_duel)
            break
        elif choice == "11":
            break
        else:
            print("Please enter 1–11.")
            input("Press Enter to continue...")


def main():
    while True:
        clear_screen()
        options = [
            "Host a LAN Game",
            "Join a LAN Game",
            "Solo / Local Games (Bingo vs Computer)",
            "Exit"
        ]
        print(render_menu("COLLEGE LAN ARCADE", options))
        choice = input("Select option: ").strip()

        if choice == "1":
            host_menu()
        elif choice == "2":
            join_lan_game()
        elif choice == "3":
            bingo.solo_setup()
        elif choice == "4":
            print("\nThanks for playing College LAN Arcade!")
            sys.exit(0)
        else:
            print("Please choose 1–4.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nArcade closed. See you next time!")
        sys.exit(0)
