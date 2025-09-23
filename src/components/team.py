from core.component import Component

PLAYER_TEAM = "player"
ENEMY_TEAM = "enemy"
NEUTRAL_TEAM = "neutral"


class Team(Component):
    def __init__(self, team_id=PLAYER_TEAM):
        self.team_id = team_id  # "player", "enemy", "neutral"
