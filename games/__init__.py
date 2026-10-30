"""
Games Package Registry.
"""
from games import bingo
from games import connect4
from games import liars_dice
from games import battleship

GAMES_REGISTRY = {
    bingo.game_id: bingo,
    connect4.game_id: connect4,
    liars_dice.game_id: liars_dice,
    battleship.game_id: battleship
}


def GET_GAME_MODULE(game_id):
    """Retrieve game module by string identifier."""
    return GAMES_REGISTRY.get(game_id, bingo)
