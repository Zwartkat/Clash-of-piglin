# src/systems/combat_system.py
import esper
from core.event_bus import EventBus
from events.death_event import DeathEvent
from components.team import Team
from components.attack import Attack
from components.health import Health
from components.target import Target
from components.position import Position
from components.stats import UnitType
from core.iterator_system import IteratingProcessor


class CombatSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Attack, Target, Position, Team)
        self.frame_count = 0

    def can_attack(
        self, ent: int, attack: Attack, ent_target_id: int, pos: Position
    ) -> bool:
        """Check if entity can attack its target"""
        if not esper.entity_exists(ent_target_id):
            return False

        # Check attack cooldown
        frames_per_attack = max(1, int(60 / attack.attack_speed))
        if self.frame_count - attack.last_attack < frames_per_attack:
            return False

        # Check range
        if not esper.has_component(ent_target_id, Position):
            return False

        target_pos: Position = esper.component_for_entity(ent_target_id, Position)
        distance_squared: int = ((target_pos.x - pos.x) ** 2) + (
            (target_pos.y - pos.y) ** 2
        )

        return distance_squared <= attack.range**2

    def process_entity(
        self,
        ent: int,
        dt: int,
        attack: Attack,
        target: Target,
        pos: Position,
        team: Team,
    ) -> None:
        """Process attacking entity"""
        self.frame_count += 1

        if not target.target_entity_id:
            return

        if self.can_attack(ent, attack, target.target_entity_id, pos):
            if not esper.has_component(target.target_entity_id, Health):
                target.target_entity_id = None
                return

            target_health: Health = esper.component_for_entity(
                target.target_entity_id, Health
            )

            # Deal damage
            old_hp: int = target_health.remaining
            target_health.remaining -= attack.damage
            attack.last_attack = self.frame_count

            # Handle death
            if target_health.remaining <= 0:
                target_health.remaining = 0
                dead_entity_id = target.target_entity_id
                EventBus.get_event_bus().emit(DeathEvent(team, dead_entity_id))
                target.target_entity_id = None
