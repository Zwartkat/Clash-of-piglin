from components.position import Position
from components.team import Team
from enums.entity_type import EntityType


class SpawnUnitEvent:

    def __init__(self, enity_type: EntityType, team: Team, position: Position):
        self.entity_type: EntityType = enity_type
        self.team: Team = team
        self.position: Position = position
