"""
Games Package Registry.
"""
from games import bingo
from games import connect4
from games import battleship
from games import dots_and_boxes
from games import tic_tac_toe
from games import hangman
from games import shiritori
from games import game2048
from games import boggle
from games import mini_crossword
from games import wordoku
from games import scrabble_sprint
from games import snake_and_ladder
from games import chess_game
from games import wordle
from games import quiz_show
from games import typing_racer
from games import artillery
from games import snake_duel
from games import sonar
from games import arrow_man

GAMES_REGISTRY = {
    bingo.game_id: bingo,
    connect4.game_id: connect4,
    battleship.game_id: battleship,
    dots_and_boxes.game_id: dots_and_boxes,
    tic_tac_toe.game_id: tic_tac_toe,
    hangman.game_id: hangman,
    shiritori.game_id: shiritori,
    game2048.game_id: game2048,
    boggle.game_id: boggle,
    mini_crossword.game_id: mini_crossword,
    wordoku.game_id: wordoku,
    scrabble_sprint.game_id: scrabble_sprint,
    snake_and_ladder.game_id: snake_and_ladder,
    chess_game.game_id: chess_game,
    wordle.game_id: wordle,
    quiz_show.game_id: quiz_show,
    typing_racer.game_id: typing_racer,
    artillery.game_id: artillery,
    snake_duel.game_id: snake_duel,
    sonar.game_id: sonar,
    arrow_man.game_id: arrow_man
}


def GET_GAME_MODULE(game_id):
    """Retrieve game module by string identifier."""
    return GAMES_REGISTRY.get(game_id, bingo)
