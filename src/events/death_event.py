from components.team import Team


class DeathEvent:
    def __init__(self, player: Team, entity: int, entity_cost: int = 0):
        self.player: Team = player
        self.entity: int = entity
        self.entity_cost: int = entity_cost
