import random
from time import time
import esper
from typing import List, Tuple

from components.base.team import Team
from components.base.cost import Cost
from core.accessors import (
    get_player_manager,
    get_world_perception,
    get_event_bus,
    get_entity,
    get_config,
)
from events.spawn_unit_event import SpawnUnitEvent
from enums.entity.entity_type import EntityType


class AiBastion:

    def __init__(self, team_id: int):
        self.team_id = team_id
        self.personality_bias = random.uniform(0.5, 1.0)
        self.rng = random.Random(
            team_id * 12345 + int(self.personality_bias * 1000) + int(time() * 1000)
        )

        config = get_config()
        tile_size = config.get("tile_size", 32)
        self.base_defense_radius = tile_size * 20

        self.money_cap = 1500
        self.surplus_threshold_base = int(self.money_cap * 0.85)

        # costs
        self.costs = {
            EntityType.BRUTE: get_entity(EntityType.BRUTE).get_component(Cost).amount,
            EntityType.CROSSBOWMAN: get_entity(EntityType.CROSSBOWMAN)
            .get_component(Cost)
            .amount,
            EntityType.GHAST: get_entity(EntityType.GHAST).get_component(Cost).amount,
        }

        # State
        self.time_since_last_counter_attack = 0.0
        self.counter_attack_cooldown_base = 60.0

        self.ghast_emergency = False

        # History for adaptiveness
        self.last_known_enemy_count = 0
        self.last_loss_count = 0

    def update(self, dt):
        wp = get_world_perception()
        player = get_player_manager().players[self.team_id]
        money = player.money

        self.time_since_last_counter_attack += dt

        base_ent, base_danger = wp.bases[self.team_id]
        enemies = self._get_enemies_near_base(wp, base_ent)
        enemy_summary = self._summarize_by_type(wp, enemies)

        # Detect ghast presence without crossbowman ally around
        if enemy_summary.get(EntityType.GHAST, 0) > 0:
            self.ghast_emergency = True
        else:
            if self._has_ally(EntityType.CROSSBOWMAN):
                self.ghast_emergency = False

        # Determine current mode
        mode = self._compute_mode(money, base_danger, enemies, wp, dt)

        # If there is a ghast emergency , run that first
        if self.ghast_emergency:
            self._run_ghast_emergency(enemy_summary, money)
            return

        # Maintain minimum guard depends on mode
        self._maintain_minimum_guard(wp, player, mode)

        # Without enemies nearby, try to attack
        if not enemies:
            if self._try_spawn_ghast(mode, player, wp):
                return
            if self._plan_counter_attack(mode, player):
                return
            self._drain_surplus(player, mode)
            return

        # 6. Enemies detected → respond based on composition
        if enemy_summary.get(EntityType.BRUTE, 0) > 0:
            self._spawn_counter_brute(enemy_summary, money, mode)
            return

        if enemy_summary.get(EntityType.CROSSBOWMAN, 0) > 0:
            self._spawn_counter_ranged(money, mode)
            return

        self._drain_surplus(player, mode)

    def _compute_mode(self, money, base_danger, enemies, wp, dt):
        """
        Compute ponderation of each mode based on current situation and return the highest score
        """

        # Data inputs
        enemy_pressure = len(enemies)
        ally_strength = self._count_allies(wp)
        losses = max(0, self.last_known_enemy_count - enemy_pressure)
        self.last_known_enemy_count = enemy_pressure

        # Initial scores
        score_aggressive = 0
        score_defensive = 0
        score_economic = 0
        score_balanced = 0

        # defensive mode prioritizes safety based on danger and pressure
        score_defensive += base_danger * 2 * self.personality_bias
        score_defensive += enemy_pressure * 1.5 * self.personality_bias
        if self.ghast_emergency:
            score_defensive += 5 * self.personality_bias

        # if there is many money and if there is enemy pressure, be more agressive
        if money > self.costs[EntityType.GHAST] + self.costs[EntityType.BRUTE]:
            score_aggressive += 1.5 * self.personality_bias
        if ally_strength > enemy_pressure + 2:
            score_aggressive += 2 * self.personality_bias
        score_aggressive += max(0, money - 400) / 200.0

        # if there is no pressure and there is no many money, be economic
        if enemy_pressure == 0:
            score_economic += 2 * self.personality_bias
        if money < 200:
            score_economic += 1.5 * self.personality_bias
        score_economic += 1 - (self.money_cap - money) / self.money_cap

        # Balanced mode
        score_balanced += 1 * self.personality_bias
        if enemy_pressure <= 1 and 0.1 < base_danger < 0.4:
            score_balanced += 1

        # Final noise
        score_aggressive += self.rng.random() * 0.3
        score_defensive += self.rng.random() * 0.3
        score_economic += self.rng.random() * 0.3
        score_balanced += self.rng.random() * 0.3

        mode = max(
            [
                ("aggressive", score_aggressive),
                ("defensive", score_defensive),
                ("economic", score_economic),
                ("balanced", score_balanced),
            ],
            key=lambda x: x[1],
        )[0]

        return mode

    def _run_ghast_emergency(self, summary, money):
        # no crossbow alive, must produce one
        if not self._has_ally(EntityType.CROSSBOWMAN):
            if not self._can_afford(EntityType.CROSSBOWMAN, money):
                return
            self.spawn_unit(EntityType.CROSSBOWMAN, self.team_id)
            return

        # otherwise, reinforce crossbows
        nb = summary.get(EntityType.GHAST, 0)
        to_spawn = nb * 2
        for _ in range(to_spawn):
            if not self._can_afford(EntityType.CROSSBOWMAN, money):
                break
            money -= self.costs[EntityType.CROSSBOWMAN]
            self.spawn_unit(EntityType.CROSSBOWMAN, self.team_id)

    def _maintain_minimum_guard(self, wp, player, mode):

        req = {
            "aggressive": {EntityType.BRUTE: 2, EntityType.CROSSBOWMAN: 1},
            "defensive": {EntityType.BRUTE: 1, EntityType.CROSSBOWMAN: 2},
            "economic": {EntityType.BRUTE: 1, EntityType.CROSSBOWMAN: 0},
            "balanced": {EntityType.BRUTE: 1, EntityType.CROSSBOWMAN: 1},
        }[mode]

        counts = {t: 0 for t in req}
        for ent, team in wp.teams.items():
            if team.team_id != self.team_id:
                continue
            et = wp.entity_types.get(ent)
            if et in counts:
                counts[et] += 1

        for et, needed in req.items():
            missing = needed - counts[et]
            for _ in range(max(0, missing)):
                if not self._can_afford(et, player.money):
                    break
                self.spawn_unit(et, self.team_id)

    def _plan_counter_attack(self, mode, player):

        # Basic wave composition to attack
        base_wave = [
            (EntityType.BRUTE, 2),
            (EntityType.CROSSBOWMAN, 1),
            (EntityType.GHAST, 1),
        ]
        self.rng.shuffle(base_wave)

        # Based on mode, change the wave a bit
        wave = self._perturb_wave(base_wave, mode)

        cooldown = (
            self.counter_attack_cooldown_base
            * {
                "aggressive": 0.7,
                "defensive": 1.4,
                "economic": 1.2,
                "balanced": 1.0,
            }[mode]
        )

        if self.time_since_last_counter_attack < cooldown:
            return False

        total_cost = sum(self.costs[et] * count for et, count in wave)
        if player.money < total_cost:
            return False

        for et, count in wave:
            for _ in range(count):
                if not self._can_afford(et, player.money):
                    return False
                self.spawn_unit(et, self.team_id)

        self.time_since_last_counter_attack = 0.0
        return True

    def _drain_surplus(self, player, mode):
        threshold = self.surplus_threshold_base

        if mode == "defensive":
            threshold *= 0.9
        elif mode == "aggressive":
            threshold *= 1.1

        while player.money > threshold:
            candidates = [EntityType.BRUTE, EntityType.CROSSBOWMAN]
            self.rng.shuffle(candidates)

            spent = False
            for et in candidates:
                if self._can_afford(et, player.money):
                    self.spawn_unit(et, self.team_id)
                    spent = True
                    break

            if not spent:
                break

    def _spawn_counter_brute(self, summary, money, mode):
        nb = summary.get(EntityType.BRUTE, 0)
        for _ in range(nb):
            if not self._can_afford(EntityType.BRUTE, money):
                return
            money -= self.costs[EntityType.BRUTE]
            self.spawn_unit(EntityType.BRUTE, self.team_id)

        # backup depends on mode
        if mode in ["defensive", "balanced"]:
            add = nb // 2 + 1
        else:
            add = nb // 2

        for _ in range(max(1, add)):
            choice = (
                EntityType.CROSSBOWMAN if self.rng.random() < 0.6 else EntityType.BRUTE
            )
            if not self._can_afford(choice, money):
                break
            money -= self.costs[choice]
            self.spawn_unit(choice, self.team_id)

    def _spawn_counter_ranged(self, money, mode):
        count = {"aggressive": 3, "defensive": 1, "economic": 2, "balanced": 2}[mode]
        for _ in range(count):
            if self._can_afford(EntityType.BRUTE, money):
                money -= self.costs[EntityType.BRUTE]
                self.spawn_unit(EntityType.BRUTE, self.team_id)

    def _try_spawn_ghast(self, mode, player, wp):
        chances = {
            "aggressive": 0.6,
            "defensive": 0.1,
            "economic": 0.4,
            "balanced": 0.3,
        }[mode]
        if self.rng.random() > chances:
            return False

        base_ent, base_danger = wp.bases[self.team_id]
        if base_danger > 0.25:
            return False
        if not self._can_afford(EntityType.GHAST, player.money):
            return False
        # Spawn max 3 ghasts
        if self._count_allies_of_type(wp, EntityType.GHAST) >= 3:
            return False

        self.spawn_unit(EntityType.GHAST, self.team_id)
        return True

    def _perturb_wave(self, wave, mode):
        out = []
        for et, count in wave:
            if et == EntityType.BRUTE:
                count += self.rng.randint(-1, 2 if mode == "aggressive" else 1)
            if et == EntityType.GHAST and mode == "aggressive":
                count += self.rng.randint(0, 1)
            out.append((et, max(1, count)))
        return out

    def _get_enemies_near_base(self, wp, base_ent):
        return [
            ent
            for ent, dist in wp.neighbors.get(base_ent, {}).items()
            if dist <= self.base_defense_radius
            and wp.teams[ent].team_id != self.team_id
        ]

    def _summarize_by_type(self, wp, entities):
        summary = {}
        for ent in entities:
            et = wp.entity_types.get(ent)
            if et:
                summary[et] = summary.get(et, 0) + 1
        return summary

    def _has_ally(self, entity_type):
        wp = get_world_perception()
        return any(
            wp.teams[e].team_id == self.team_id
            and wp.entity_types.get(e) == entity_type
            for e in wp.teams
        )

    def _count_allies(self, wp):
        return sum(1 for e, t in wp.teams.items() if t.team_id == self.team_id)

    def _count_allies_of_type(self, wp, t):
        return sum(
            1
            for e, tm in wp.teams.items()
            if tm.team_id == self.team_id and wp.entity_types.get(e) == t
        )

    def _can_afford(self, et, money):
        return money >= self.costs.get(et, 999999)

    def spawn_unit(self, et, team_id):
        player = get_player_manager().players[team_id]
        pos = player.spawn_position
        get_event_bus().emit(SpawnUnitEvent(et, Team(team_id), pos))
        player.money -= self.costs[et]
