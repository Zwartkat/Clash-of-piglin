# src/systems/combat_system.py
import esper
from core.accessors import get_event_bus
from core.ecs.event_bus import EventBus
from events.attack_event import AttackEvent
from events.death_event import DeathEvent
from events.arrow_fired_event import ArrowFiredEvent
from components.base.team import Team
from components.gameplay.attack import Attack
from components.base.health import Health
from components.gameplay.target import Target
from components.base.position import Position
from core.ecs.iterator_system import IteratingProcessor
from components.base.cost import Cost
from enums.entity.entity_type import EntityType


class CombatSystem(IteratingProcessor):
    """Handles combat between entities with attack and target components."""

    def __init__(self):
        super().__init__(Attack, Target, Position, Team)
        self.frame_count = 0

    def can_attack(
        self, ent: int, attack: Attack, ent_target_id: int, pos: Position
    ) -> bool:
        """
        Check if entity can attack its current target.

        Args:
            ent: Attacking entity ID
            attack: Entity attack stats and cooldown info
            ent_target_id: Target entity ID to attack
            pos: Attacker position on map

        Returns:
            bool: True if entity can attack target now
        """
        if not esper.entity_exists(ent_target_id):
            return False

        # Check attack cooldown based on attack speed
        frames_per_attack = max(1, int(60 * attack.attack_speed))
        if self.frame_count - attack.last_attack < frames_per_attack:
            return False

        # Check if target is in attack range
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
        """
        Process one attacking entity and handle damage dealing.

        Args:
            ent: Attacking entity ID
            dt: Time passed since last frame
            attack: Entity attack damage and cooldown data
            target: Entity current target info
            pos: Attacker position on map
            team: Attacker team for death event
        """
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

            target_pos: Position = esper.component_for_entity(
                target.target_entity_id, Position
            )

            # Fire arrow if attacker is a Crossbowman
            components = esper.components_for_entity(ent)
            for component in components:
                if (
                    isinstance(component, EntityType)
                    and component == EntityType.CROSSBOWMAN
                ):
                    get_event_bus().emit(ArrowFiredEvent(ent, pos, target_pos))
                    break

            # Apply damage to target
            get_event_bus().emit(AttackEvent(ent, target.target_entity_id))

            # Deal damage
            old_hp: int = target_health.remaining
            target_health.remaining -= attack.damage
            attack.last_attack = self.frame_count

            # Handle target death
            if target_health.remaining <= 0:
                target_health.remaining = 0
                dead_entity_id = target.target_entity_id
                # Get entity cost before emitting death event

                entity_cost = 0

                if esper.has_component(dead_entity_id, Cost):
                    cost_component = esper.component_for_entity(dead_entity_id, Cost)
                    entity_cost = cost_component.amount
                    get_event_bus().emit(DeathEvent(team, dead_entity_id, entity_cost))
                target.target_entity_id = None
