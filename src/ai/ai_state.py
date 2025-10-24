import math
import esper

from components.base.health import Health
from components.base.position import Position
from components.base.team import Team
from components.gameplay.attack import Attack
from components.gameplay.target import Target
from core.accessors import get_config
from enums.config_key import ConfigKey
from enums.entity.action import ActionType
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType


class AiState:
    def __init__(self, ent: int):
        self.entity: int = ent
        self.pos: Position = esper.component_for_entity(self.entity, Position)
        self.team: Team = esper.component_for_entity(self.entity, Team)
        self.atk: Attack = esper.component_for_entity(self.entity, Attack)
        self.health: Health = esper.component_for_entity(self.entity, Health)
        self.target: Target = esper.component_for_entity(self.entity, Target)

        if not esper.has_component(self.entity, Target) or self.target is None:
            self.target = Target()
            esper.add_component(self.entity, self.target)

        self.destination: tuple[int, int] | None = None
        self.path: list[tuple[int, int]] = []

        self.action: ActionType | None = None

        self.health_ratio: float = 1.0

        # entity_id -> [Position, distance]
        self.ennemies: dict[int, list[Position, float]] = {}
        # entity_id -> [Position, distance, health_ratio, danger_score]
        self.allies: dict[int, list[Position, float, float, float]] = {}

        self.in_attack_range: bool = False

        self.nearest_enemy: tuple[int, int] | None = None
        self.nearest_ally: tuple[int, int] | None = None

        self.weakness_ally: int | None = None

        self._tile_size = get_config().get(ConfigKey.TILE_SIZE.value)
        self.vision_range: int = self._tile_size * 4

        self.in_combat: bool = False
        self.combat_time: float = 0

        self.under_attack: bool = False
        self.time_since_last_hit: float = 0

        self.can_attack: bool = True
        self.atk.last_attack = 0

        self.alert_level: float = 0

    def perceive(self, dt):

        self.ennemies = {}
        self.allies = {}
        self.nearest_enemy = None
        self.nearest_ally = None

        self.health_ratio = self.health.remaining / self.health.full

        self.time_since_last_hit += dt
        self.under_attack = self.time_since_last_hit < 2

        self.atk.last_attack += dt
        self.can_attack = self.atk.last_attack > self.atk.attack_speed

        for e, (pos, team, unit_type, entity_type, health) in esper.get_components(
            Position, Team, UnitType, EntityType, Health
        ):
            if e == self.entity:
                continue

            if (
                team.team_id != self.team.team_id
                and unit_type not in self.target.allow_targets
                and entity_type not in self.target.allow_targets
            ):
                continue

            dx = pos.x - self.pos.x
            dy = pos.y - self.pos.y
            dist = math.hypot(dx, dy)

            # Register all entities within vision range
            if dist <= self.vision_range:
                if team.team_id != self.team.team_id:
                    self.ennemies[e] = [pos, dist]
                    if self.nearest_enemy is None or dist < self.nearest_enemy[1]:
                        self.nearest_enemy = (e, dist)
                else:
                    health_ratio: float = health.remaining / health.full
                    danger_score: float = (1 - health_ratio) * 0.5 + (
                        1 - dist / self.vision_range
                    ) * 0.3
                    self.allies[e] = [pos, dist, health_ratio, danger_score]
                    if self.nearest_ally is None or dist < self.nearest_ally[1]:
                        self.nearest_ally = (e, dist)
                    if (
                        self.weakness_ally is None
                        or self.weakness_ally not in self.allies
                        or danger_score > self.allies[self.weakness_ally][3]
                    ):
                        self.weakness_ally = e
        if self.nearest_enemy is not None:
            self.target.target_entity_id = self.nearest_enemy[0]
            self.in_attack_range = self.nearest_enemy[1] < self.atk.range
        else:
            self.in_attack_range = False

        for ally_id, (ally_pos, _, _, _) in self.allies.items():
            threats = []
            for enemy_pos, _ in self.ennemies.values():
                dist = math.hypot(ally_pos.x - enemy_pos.x, ally_pos.y - enemy_pos.y)
                threat = max(0.0, 1 - dist / (self.vision_range))
                threats.append(threat)
            nearby_enemy_threat = sum(threats) / max(1, len(self.ennemies))
            # print(nearby_enemy_threat)

    def evaluate_context(self, dt):

        if self.under_attack:
            self.alert_level = min(1.0, self.alert_level + dt)
        else:
            self.alert_level = max(0.0, self.alert_level - dt * 0.5)

        if self.allies:
            self.alert_level = max(0.0, self.alert_level - dt * len(self.allies))

        if self.ennemies:
            self.alert_level = min(1.0, self.alert_level + dt * 2 * len(self.ennemies))
            self.in_combat = True
            self.combat_time += dt
        else:
            self.alert_level = max(0.0, self.alert_level - dt)
            self.in_combat = False
            self.combat_time = 0

        if self.weakness_ally and self.weakness_ally in self.allies:
            _, _, _, danger_score = self.allies[self.weakness_ally]
            if danger_score < 0.6:
                self.weakness_ally = None
        else:
            self.weakness_ally = None

    def update(self, dt):
        self.perceive(dt)
        self.evaluate_context(dt)
