import copy

import esper

from components.base.cost import Cost
from components.gameplay.effects import OnTerrain
from components.base.position import Position
from components.base.team import Team
from core.accessors import get_debugger, get_entity
from core.ecs.entity import Entity
from enums.entity.entity_type import EntityType
from events.spawn_unit_event import SpawnUnitEvent
from factories.entity_factory import EntityFactory


class UnitFactory:
    """Creates game units and squads from entity type definitions."""

    @staticmethod
    def create_unit(entity_type: EntityType, team: Team, position: Position):
        """
        Create a single unit entity of specified type.

        Args:
            entity_type: Type of unit to create (sword, crossbow, ghast, etc.)
            team: Which team this unit belongs to
            position: Starting position on the map

        Returns:
            int: Created entity ID number

        Raises:
            ValueError: If entity_type is not found in unit config
        """
        entity: Entity = get_entity(entity_type)
        if not entity:
            raise ValueError(f"Unknown unit type: {entity_type}")

        # Replace template position/team with actual values
        components = entity.get_all_components()
        components = [c for c in components if not isinstance(c, (Position, Team))]
        components.append(position)
        components.append(team)
        components.append(OnTerrain())  # Required for terrain effects

        ent: int = EntityFactory.create(*components)

        if entity_type == EntityType.BRUTE or entity_type == EntityType.GHAST:
            from components.ai_controller import AIController

            esper.add_component(ent, AIController(ent, entity_type))

        return ent

    @staticmethod
    def create_unit_event(event: SpawnUnitEvent):
        UnitFactory.create_unit(event.entity_type, event.team, event.position)

    @staticmethod
    def create_squad(entity_type: EntityType, positions: list[Position], team: Team):
        """
        Create multiple units of same type at different positions.

        Args:
            entity_type: Type of units to create
            positions: List of positions where units will spawn
            team: Which team all units belong to

        Returns:
            list[int]: List of created entity ID numbers
        """
        entities: list[int] = []

        for pos in positions:
            entity: int = UnitFactory.create_unit(entity_type, team, pos)
            entities.append(entity)
        return entities

    @staticmethod
    def get_unit_cost(entity_type: EntityType) -> int:
        """
        Get gold cost to purchase this unit type.

        Args:
            entity_type: Type of unit to check price for

        Returns:
            int: Gold cost amount, or 0 if unit type not found
        """
        entity: Entity = get_entity(entity_type)
        if not entity:
            return 0
        cost: Cost = entity.get_component(Cost)
        return cost.amount
