"""
Games Package Registry.
"""
from games import bingo
from games import connect4
from games import liars_dice
from games import battleship
from games import uno
from games import dots_and_boxes
from games import tic_tac_toe
from games import mastermind

GAMES_REGISTRY = {
    bingo.game_id: bingo,
    connect4.game_id: connect4,
    liars_dice.game_id: liars_dice,
    battleship.game_id: battleship,
    uno.game_id: uno,
    dots_and_boxes.game_id: dots_and_boxes,
    tic_tac_toe.game_id: tic_tac_toe,
    mastermind.game_id: mastermind
}


def GET_GAME_MODULE(game_id):
    """Retrieve game module by string identifier."""
    return GAMES_REGISTRY.get(game_id, bingo)
