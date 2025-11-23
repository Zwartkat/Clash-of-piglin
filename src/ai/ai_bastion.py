# spawn_manager.py

from ai.ai_state import AiState
from ai.world_perception import WorldPerception
from components.base.cost import Cost
from components.base.team import Team
from core.accessors import (
    get_config,
    get_entity,
    get_event_bus,
    get_player_manager,
    get_world_perception,
)
from enums.entity.entity_type import EntityType
from events.spawn_unit_event import SpawnUnitEvent
from factories.unit_factory import UnitFactory
from enums.entity.unit_type import UnitType


class AiBastion(AiState):
    """
    Bastion Ai who manage spawn of units based on:
    - enemy presence
    - available money
    """

    def __init__(self, team_id: int):
        self.team_id = team_id

        self.base_defense_radius = get_config().get("tile_size", 32) * 10

        self.costs = {
            EntityType.BRUTE: (get_entity(EntityType.BRUTE).get_component(Cost)).amount,
            EntityType.CROSSBOWMAN: (
                get_entity(EntityType.CROSSBOWMAN).get_component(Cost)
            ).amount,
            EntityType.GHAST: (get_entity(EntityType.GHAST).get_component(Cost)).amount,
        }

    def update(self, dt):

        world_perception = get_world_perception()

        base_entity, _ = world_perception.bases[self.team_id]
        money = get_player_manager().players[self.team_id].money

        enemies = self._get_enemies_near_base(world_perception, base_entity)

        if not enemies:
            self._attack_setup(money)
            return

        summary = self._summarize_by_entity_type(world_perception, enemies)

        if summary.get(EntityType.GHAST, 0) > 0:
            self._spawn_counter_ghast(summary, money)
            return

        if summary.get(EntityType.BRUTE, 0) > 0:
            self._spawn_counter_brute(summary, money)
            return

        if summary.get(EntityType.CROSSBOWMAN, 0) > 0:
            self._spawn_counter_ranged(money)
            return

    def _attack_setup(self, money):
        """
        Attack enemy bastion if there is no enemy
        """
        needed = [
            (EntityType.BRUTE, 2),
            (EntityType.CROSSBOWMAN, 1),
        ]

        for unit_type, count in needed:
            for _ in range(count):
                if self._can_afford(unit_type, money):
                    money -= self.costs[unit_type]
                    self.spawn_unit(unit_type, self.team_id)

    def _spawn_counter_ghast(self, summary, money):

        nb_ghast = summary.get(EntityType.GHAST, 0)
        to_spawn = nb_ghast * 2

        for _ in range(to_spawn):
            if not self._can_afford(EntityType.CROSSBOWMAN, money):
                break
            money -= self.costs[EntityType.CROSSBOWMAN]
            self.spawn_unit(EntityType.CROSSBOWMAN, self.team_id)

    def _spawn_counter_brute(self, summary, money):
        nb_brutes = summary.get(EntityType.BRUTE, 0)

        # frontline brute
        for _ in range(nb_brutes):
            if not self._can_afford(EntityType.BRUTE, money):
                break
            money -= self.costs[EntityType.BRUTE]
            self.spawn_unit(EntityType.BRUTE, self.team_id)

        # backup ranged
        archers_to_spawn = max(1, nb_brutes // 2)
        for _ in range(archers_to_spawn):
            if not self._can_afford(EntityType.CROSSBOWMAN, money):
                break
            money -= self.costs[EntityType.CROSSBOWMAN]
            self.spawn_unit(EntityType.CROSSBOWMAN, self.team_id)

    def _spawn_counter_ranged(self, money):
        """
        Contre archer/arbalétrier ennemi → brute
        """
        for _ in range(2):
            if not self._can_afford(EntityType.BRUTE, money):
                break
            money -= self.costs[EntityType.BRUTE]
            self.spawn_unit(EntityType.BRUTE, self.team_id)

    def _get_enemies_near_base(
        self, world_perception: WorldPerception, base_entity: int
    ):
        enemies = []
        for ent, dist in world_perception.neighbors.get(base_entity, {}).items():
            if dist <= self.base_defense_radius:
                if world_perception.teams[ent].team_id != self.team_id:
                    enemies.append(ent)
        return enemies

    def _summarize_by_entity_type(self, world_perception: WorldPerception, enemy_list):
        summary = {}
        for ent in enemy_list:
            entity_type = world_perception.entity_types.get(ent)
            if entity_type:
                summary[entity_type] = summary.get(entity_type, 0) + 1
        return summary

    def _can_afford(self, entity_type: EntityType, money: int):
        return money >= self.costs.get(entity_type, 9999)

    def spawn_unit(self, entity_type: EntityType, team_id: int):
        """
        Spawn a unit of given type for given team.
        """
        player = get_player_manager().players[team_id]
        spawn_position = player.spawn_position
        team = Team(team_id)
        get_event_bus().emit(SpawnUnitEvent(entity_type, Team(team_id), spawn_position))
        player.money -= self.costs.get(entity_type, 0)
