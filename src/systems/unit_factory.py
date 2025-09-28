import copy
import esper

from components.cost import Cost
from components.position import Position
from components.sprite import Sprite
from components.velocity import Velocity
from components.collider import Collider
from components.team import Team
from components.attack import Attack
from components.selection import Selection
from components.effects import OnTerrain
from components.health import Health
from components.stats import UnitType
from config.units import UNITS
from core.entity import Entity
from enums.entity_type import EntityType
from systems.entity_factory import EntityFactory


class UnitFactory:
    @staticmethod
    def create_unit(entity_type: EntityType, team: Team, position: Position):
        entity: Entity = copy.deepcopy(UNITS.get(entity_type, None))
        if not entity:
            raise ValueError(f"Unknown unit type: {entity_type}")

        components = []

        for comp in entity.get_all_components():
            components.append(copy.deepcopy(comp))

        components = [c for c in components if not isinstance(c, (Position, Team))]
        components.append(position)
        components.append(team)
        components.append(OnTerrain())

        ent: int = EntityFactory.create(*components)

        return ent

    @staticmethod
    def create_squad(entity_type: EntityType, positions: list[Position], team: Team):

        entities: list[int] = []

        for pos in positions:
            entity: int = UnitFactory.create_unit(entity_type, team, pos)
            entities.append(entity)
        return entities

    @staticmethod
    def get_unit_cost(entity_type: EntityType) -> int:
        entity: Entity = UNITS.get(entity_type, None)
        if not entity:
            return 0
        cost: Cost = entity.get_component(Cost)
        return cost.amount
