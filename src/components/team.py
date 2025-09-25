from core.component import Component

PLAYER_1_TEAM = 1
PLAYER_2_TEAM = 2
NEUTRAL_TEAM = 0


class Team(Component):
    def __init__(self, team_id=PLAYER_1_TEAM):
        self.team_id = team_id
