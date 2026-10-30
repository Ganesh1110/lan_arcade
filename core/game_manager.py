"""
GameManager loads game modules and enforces the unified game interface.
"""
from core.exceptions import InvalidMoveError


class GameManager:
    def __init__(self, game_module):
        self.module = game_module
        self.state = None

    def initialize(self, player_sessions):
        """Create initial game state using player list."""
        self.state = self.module.create_state(player_sessions)
        return self.state

    def current_player_id(self):
        """Return the player_id whose turn it currently is."""
        return self.module.current_player(self.state)

    def get_view_for(self, player_id):
        """Return private game view payload for a specific player."""
        return self.module.view_for(self.state, player_id)

    def get_prompt_for(self, player_id):
        """Return prompt string for input."""
        return self.module.prompt_for(self.state, player_id)

    def parse_and_apply(self, player_id, raw_action):
        """
        Validate and apply an action from player_id.
        Raises InvalidMoveError if invalid.
        Returns result payload from apply_action.
        """
        if self.current_player_id() != player_id:
            raise InvalidMoveError("It is not your turn.")

        valid, result_or_err = self.module.parse_action(self.state, player_id, raw_action)
        if not valid:
            raise InvalidMoveError(str(result_or_err))

        return self.module.apply_action(self.state, player_id, result_or_err)

    def is_over(self):
        """Check if current game has reached an end condition."""
        return self.module.is_over(self.state)

    def get_winner(self):
        """Return list of winner names/info."""
        return self.module.get_winner(self.state)

    def skip_player(self, player_id):
        """Handle disconnected player skip logic if module supports it."""
        if hasattr(self.module, "skip_player"):
            self.module.skip_player(self.state, player_id)
