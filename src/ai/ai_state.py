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

        self.destination: tuple[int, int] | None = None
        self.path: list[tuple[int, int]] = []

        self.action: ActionType | None = None

        self.health_ratio: float = 1.0

        self.ennemies: dict[int, tuple[Position, float]] = {}
        self.allies: dict[int, tuple[Position, float]] = {}

        self.in_attack_range: bool = False

        self.nearest_enemy: tuple[int, int] | None = None
        self.nearest_ally: tuple[int, int] | None = None

        self.vision_range_sq: int = (
            get_config().get(ConfigKey.TILE_SIZE.value) * 5
        ) ** 2

        self.in_combat: bool = False
        self.combat_time: float = 0

        self.under_attack: bool = False
        self.time_since_last_hit: float = 0

        self.can_attack: bool = True
        self.time_since_last_atk: float = 0

        self.alert_level: float = 0

    def perceive(self, dt):

        self.ennemies = {}
        self.allies = {}
        self.nearest_enemy = None
        self.nearest_ally = None

        self.health_ratio = self.health.remaining / self.health.full

        self.time_since_last_hit += dt
        self.under_attack = self.time_since_last_hit < 2

        self.time_since_last_atk += dt
        self.can_attack = self.time_since_last_atk > self.atk.attack_speed

        for e, (pos, team, unit_type, entity_type) in esper.get_components(
            Position, Team, UnitType, EntityType
        ):
            if e == self.entity:
                continue

            if (
                self.target
                and team.team_id != self.team.team_id
                and unit_type not in self.target.allow_targets
                and entity_type not in self.target.allow_targets
            ):
                continue

            dx = pos.x - self.pos.x
            dy = pos.y - self.pos.y
            dist_sq = (dx * dx) + (dy * dy)

            if dist_sq <= self.vision_range_sq:
                if team.team_id != self.team.team_id:
                    self.ennemies[e] = (pos, dist_sq)
                    if self.nearest_enemy is None or dist_sq < self.nearest_enemy[1]:
                        self.nearest_enemy = (e, dist_sq)
                else:
                    self.allies[e] = (pos, dist_sq)
                    if self.nearest_ally is None or dist_sq < self.nearest_ally[1]:
                        self.nearest_ally = (e, dist_sq)
        if self.nearest_enemy is not None:
            self.target.target_entity_id = self.nearest_enemy[0]
            self.in_attack_range = self.nearest_enemy[1] < self.atk.range**2
        else:
            self.in_attack_range = False

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

    def update(self, dt):
        self.perceive(dt)
        self.evaluate_context(dt)
