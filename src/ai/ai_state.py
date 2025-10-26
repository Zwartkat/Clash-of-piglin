import math
from time import sleep
import esper

from ai.world_perception import WorldPerception
from components.base.health import Health
from components.base.position import Position
from components.base.team import Team
from components.gameplay.attack import Attack
from components.gameplay.target import Target
from core.accessors import get_config, get_map, get_player_manager
from enums.config_key import ConfigKey
from enums.entity.action import ActionType
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType


class AiState:
    def __init__(self, ent: int):
        """
        Initialize AI state for a given entity.

        Args:
            ent (int): Entity ID controlled by this AI.
        """
        # Components of current entity
        self.entity: int = ent
        self.pos: Position = esper.component_for_entity(self.entity, Position)
        self.team: Team = esper.component_for_entity(self.entity, Team)
        self.atk: Attack = esper.component_for_entity(self.entity, Attack)
        self.health: Health = esper.component_for_entity(self.entity, Health)
        self.target: Target = esper.component_for_entity(self.entity, Target)

        if not esper.has_component(self.entity, Target) or self.target is None:
            self.target = Target()
            esper.add_component(self.entity, self.target)

        self.world_perception: WorldPerception = None

        self.action_weights: dict[Action, float] = {}

        self.health_ratio: float = 1.0

        # Movement / Pathfinding
        self.destination: tuple[int, int] | None = None
        self.path: list[tuple[int, int]] = []

        # Nearby entities

        # entity_id -> [Position, distance]
        self.enemies: dict[int, list[Position, float]] = {}
        # entity_id -> [Position, distance, health_ratio, danger_score]
        self.allies: dict[int, list[Position, float, float, float]] = {}

        self.in_attack_range: bool = False

        self.nearest_enemy: tuple[int, Position, float] | None = None
        self.nearest_ally: tuple[int, Position, float] | None = None

        self.weakness_ally: int | None = None

        # Combat
        self.in_combat: bool = False
        self.combat_time: float = 0

        self.under_attack: bool = False
        self.time_since_last_hit: float = 0

        self.can_attack: bool = True
        self.atk.last_attack = 0

        self.alert_level: float = 0

        self.base_under_attack = False
        self.ally_base: int = get_player_manager().get_current_player().bastion
        self.ally_base_pos: Position = esper.component_for_entity(
            self.ally_base, Position
        )

        self.enemy_base: int = (
            get_player_manager().get_enemy_player(self.team.team_id).bastion
        )
        self.enemy_base_pos: Position = esper.component_for_entity(
            self.enemy_base, Position
        )

        # Config
        self._tile_size = get_config().get(ConfigKey.TILE_SIZE.value)
        self.vision_range: int = self._tile_size * 4

    def perceive(self, world_perception: WorldPerception, dt: float) -> None:
        """
        Update the AI's perception of the world.
        - Reset previous perceptions
        - Update health and attack timers
        - Detect nearby entities
        - Calculate threats for allies

        Args:
            dt (float): Delta time since last update
        """

        if not self.world_perception:
            self.world_perception = world_perception

        self._reset_perception()
        self._update_attack(dt)

        for ent2, dist in world_perception.neighbors.get(self.entity, {}).items():
            team2 = world_perception.teams[ent2]
            pos2 = world_perception.positions[ent2]
            health_ratio = world_perception.health_ratios.get(ent2, 1.0)
            danger_score = world_perception.danger_scores.get(ent2, 0.0)

            if team2.team_id != self.team.team_id:
                self.enemies[ent2] = [pos2, dist]

                if not self.nearest_enemy or dist < self.nearest_enemy[2]:
                    self.nearest_enemy = (ent2, pos2, dist)
            else:
                self.allies[ent2] = [pos2, dist, health_ratio, danger_score]

                if not self.nearest_ally or dist < self.nearest_ally[2]:
                    self.nearest_ally = (ent2, pos2, dist)
                if (
                    not self.weakness_ally
                    or self.weakness_ally not in self.allies
                    or danger_score > self.allies[self.weakness_ally][3]
                ):
                    self.weakness_ally = ent2

        self.in_attack_range = (
            self.nearest_enemy and self.nearest_enemy[2] < self.atk.range
        )
        if self.nearest_enemy:
            self.target.target_entity_id = self.nearest_enemy[0]

    def _reset_perception(self):
        self.nearest_enemy = None
        self.nearest_ally = None
        self.enemies.clear()
        self.allies.clear()
        self.weakness_ally = None

    def _update_attack(self, dt: float) -> None:
        """
        Update health ratio, attack cooldowns and under-attack status.

        Args:
            dt (float): Delta time since last update
        """
        if self.under_attack:
            self.time_since_last_hit += dt
        self.under_attack = self.time_since_last_hit > 2
        if not self.can_attack:
            self.atk.last_attack += dt
        self.can_attack = self.atk.last_attack > self.atk.attack_speed

    def evaluate_context(self, dt: float) -> None:
        """
        Evaluate the context and update internal state:
        - Alert level
        - Combat status
        - Weakest ally
        - Emotional action weights

        Args:
            dt (float): Delta time since last update
        """
        self._update_alert_level(dt)
        self._update_combat_status(dt)
        self._update_weakness_ally()
        self._evaluate_action_weights()

    def _update_alert_level(self, dt: float) -> None:
        """
        Update alert level based on:
        - Being under attack
        - Number of enemies and allies nearby
        """
        if self.under_attack:
            self.alert_level = min(1.0, self.alert_level + dt * 5)
        else:
            self.alert_level = max(0.0, self.alert_level - dt * 0.1)

        if self.allies:
            self.alert_level = max(
                0.0, self.alert_level - (dt * len(self.allies) // 10)
            )

        if self.enemies:
            self.alert_level = min(1.0, self.alert_level + dt * 2 * len(self.enemies))

    def _update_combat_status(self, dt: float) -> None:
        """
        Update whether the AI is in combat and track combat duration.
        """
        self.in_combat = bool(self.enemies)
        self.combat_time = self.combat_time + dt if self.in_combat else 0

    def _update_weakness_ally(self) -> None:
        """
        Clear weakness ally if there is no more in allies list
        """
        if not self.allies or self.weakness_ally not in self.allies:
            self.weakness_ally = None

    def _evaluate_action_weights(self) -> None:
        """
        Evaluate the weight of actions based on emotional dimensions:
        - AGGRO, FEAR, SOLIDARITY, GOAL
        - GOAL now reflects attraction to strategic objectives like enemy base
        - Action weights are normalized between 0 and 1
        """

        num_enemies = len(self.enemies)
        num_allies = len(self.allies)

        # Threat perception
        threat_level = min(1.0, num_enemies / 5.0)
        ally_support = min(1.0, num_allies / 5.0)

        # Stress factor
        under_attack_factor = 1.0 if self.under_attack else 0.0

        # Distance to nearest enemy (0 if close, 1 if far)
        dist_factor = 0.0
        if self.nearest_enemy:
            dist = self.nearest_enemy[2]
            dist_factor = max(0.0, 1.0 - dist / self.vision_range)

        self._emotions = {}

        # Aggressivity: depends on alert level, enemy proximity and ally support
        self._emotions[Emotion.AGGRO] = (
            0.8 * self.alert_level + 0.2 * dist_factor + 0.1 * ally_support
        )

        # Fear: low health, under attack and isolation
        self._emotions[Emotion.FEAR] = (
            (1 - self.health_ratio) * 0.7
            + under_attack_factor * 0.2
            + (1 - ally_support) * 0.1
        )

        # Solidarity: hurted ally and ally presence
        avg_ally_danger = (
            sum(a[3] for a in self.allies.values()) / num_allies if num_allies else 0
        )
        self._emotions[Emotion.SOLIDARITY] = avg_ally_danger

        # Goal: attraction to strategic goal, reduced if alert level high
        self._emotions[Emotion.GOAL] = max(0.0, 1.0 - self.alert_level)
        # print("-----------------------------\n")
        # print(self.entity,self._emotions,self.alert_level, self.under_attack, self.enemies)

        # Calculate action weights from emotions
        e = self._emotions
        self.action_weights[Action.ATTACK] = e[Emotion.AGGRO] - 0.2 * e[Emotion.FEAR]
        self.action_weights[Action.PROTECT] = (
            0.5 * e[Emotion.SOLIDARITY] + 0.3 * e[Emotion.AGGRO]
        )
        self.action_weights[Action.RETREAT] = e[Emotion.FEAR] + e[Emotion.AGGRO]
        self.action_weights[Action.GOAL] = e[Emotion.GOAL]
        self.action_weights[Action.DEFEND_BASE] = self.world_perception.bases[
            self.team.team_id
        ][1]

        # Clamp values to [0,1]
        for k, weight in self.action_weights.items():
            self.action_weights[k] = max(0.0, min(1.0, round(weight, 3)))

        # Normalize weights
        max_w = max(self.action_weights.values()) or 1.0
        if max_w > 0:
            for k in self.action_weights:
                self.action_weights[k] = round(self.action_weights[k] / max_w, 3)
        # print(self.action_weights[Action.DEFEND_BASE])

    def update(self, wordl_perception: WorldPerception, dt: float) -> None:
        """
        Update AI state for the current frame:
        - Perceive surroundings
        - Evaluate context and emotional weights

        Args:
            dt (float): Delta time since last update
        """
        self.perceive(wordl_perception, dt)
        self.evaluate_context(dt)


from enum import Enum, auto


class Emotion(Enum):
    AGGRO = auto()
    FEAR = auto()
    SOLIDARITY = auto()
    GOAL = auto()


class Action(Enum):
    ATTACK = auto()
    PROTECT = auto()
    RETREAT = auto()
    GOAL = auto()
    DEFEND_BASE = auto()
