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

        config = get_config()

        self.base_defense_radius = config.get("tile_size", 32) * 10
        self.money_cap = config.get("money_cap", 1500)
        self.surplus_threshold = int(self.money_cap * 0.85)

        self.costs = {
            EntityType.BRUTE: (get_entity(EntityType.BRUTE).get_component(Cost)).amount,
            EntityType.CROSSBOWMAN: (
                get_entity(EntityType.CROSSBOWMAN).get_component(Cost)
            ).amount,
            EntityType.GHAST: (get_entity(EntityType.GHAST).get_component(Cost)).amount,
        }

        self.guard_buffer_cost = (
            self.costs[EntityType.BRUTE] + self.costs[EntityType.CROSSBOWMAN]
        )

        self.counter_attack_wave = [
            (EntityType.BRUTE, 2),
            (EntityType.CROSSBOWMAN, 2),
        ]
        self.counter_attack_cooldown = 20.0
        self.time_since_last_counter_attack = self.counter_attack_cooldown
        self.counter_attack_budget = sum(
            self.costs[entity_type] * count
            for entity_type, count in self.counter_attack_wave
        )

    def update(self, dt):

        world_perception = get_world_perception()
        player = get_player_manager().players[self.team_id]

        self.time_since_last_counter_attack += dt
        self._maintain_minimum_guard(world_perception, player)

        base_entity, _ = world_perception.bases[self.team_id]
        money = player.money

        enemies = self._get_enemies_near_base(world_perception, base_entity)

        if not enemies:
            launched = self._plan_counter_attack(player)
            if not launched:
                self._drain_surplus_gold(player)
            return

        summary = self._summarize_by_entity_type(world_perception, enemies)

        if summary.get(EntityType.GHAST, 0) > 0:
            self._spawn_counter_ghast(summary, money)
            self._drain_surplus_gold(player)
            return

        if summary.get(EntityType.BRUTE, 0) > 0:
            self._spawn_counter_brute(summary, money)
            self._drain_surplus_gold(player)
            return

        if summary.get(EntityType.CROSSBOWMAN, 0) > 0:
            self._spawn_counter_ranged(money)
            self._drain_surplus_gold(player)
            return

        self._drain_surplus_gold(player)

    def _maintain_minimum_guard(self, world_perception: WorldPerception, player):
        """Ensure at least one brute and one crossbowman stay alive."""
        guard_requirements = {
            EntityType.BRUTE: 1,
            EntityType.CROSSBOWMAN: 1,
        }

        friendly_counts = {entity_type: 0 for entity_type in guard_requirements}

        for ent, team in world_perception.teams.items():
            if team.team_id != self.team_id:
                continue
            entity_type = world_perception.entity_types.get(ent)
            if entity_type in friendly_counts:
                friendly_counts[entity_type] += 1

        guard_priority = [EntityType.BRUTE, EntityType.CROSSBOWMAN]

        for entity_type in guard_priority:
            desired = guard_requirements[entity_type]
            current = friendly_counts.get(entity_type, 0)
            missing = max(0, desired - current)

            for _ in range(missing):
                if not self._can_afford(entity_type, player.money):
                    break
                self.spawn_unit(entity_type, self.team_id)

    def _plan_counter_attack(self, player):
        """Stockpile gold and launch a predefined wave when conditions are met."""
        if self.time_since_last_counter_attack < self.counter_attack_cooldown:
            return False

        if player.money < self.counter_attack_budget:
            return False

        for entity_type, count in self.counter_attack_wave:
            for _ in range(count):
                if not self._can_afford(entity_type, player.money):
                    return False
                self.spawn_unit(entity_type, self.team_id)

        self.time_since_last_counter_attack = 0.0
        return True

    def _drain_surplus_gold(self, player):
        """Spend excess gold so we never hit the money cap while idle."""

        target_threshold = max(self.surplus_threshold, self.guard_buffer_cost)
        if player.money <= target_threshold:
            return

        reserve = max(self.counter_attack_budget, self.guard_buffer_cost)

        filler_cycle = [EntityType.BRUTE, EntityType.CROSSBOWMAN]

        while player.money > target_threshold:
            spent = False
            for entity_type in filler_cycle:
                cost = self.costs[entity_type]
                if not self._can_afford(entity_type, player.money):
                    continue
                if player.money - cost < reserve:
                    continue
                self.spawn_unit(entity_type, self.team_id)
                spent = True
                break

            if not spent:
                break

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
