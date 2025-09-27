from components.team import Team


class DeathEvent:
    def __init__(self, player: Team, entity: int):
        self.player: Team = player
        self.entity: int = entity
