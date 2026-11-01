"""
Games Package Registry.
"""
from games import bingo
from games import connect4
from games import battleship
from games import dots_and_boxes
from games import tic_tac_toe
from games import hangman
from games import rock_paper_scissors
from games import shiritori
from games import game2048
from games import number_duel

GAMES_REGISTRY = {
    bingo.game_id: bingo,
    connect4.game_id: connect4,
    battleship.game_id: battleship,
    dots_and_boxes.game_id: dots_and_boxes,
    tic_tac_toe.game_id: tic_tac_toe,
    hangman.game_id: hangman,
    rock_paper_scissors.game_id: rock_paper_scissors,
    shiritori.game_id: shiritori,
    game2048.game_id: game2048,
    number_duel.game_id: number_duel
}


def GET_GAME_MODULE(game_id):
    """Retrieve game module by string identifier."""
    return GAMES_REGISTRY.get(game_id, bingo)
