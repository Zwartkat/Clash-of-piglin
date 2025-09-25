class PlayerManager:
    def __init__(self):
        self.current_player = 1

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
        print(f"Current player switched to: {self.current_player}")

    def get_current_player(self):
        return self.current_player

    def is_current_player_entity(self, team_id):
        return team_id == self.get_current_player()
