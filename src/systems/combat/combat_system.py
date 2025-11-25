# src/systems/combat_system.py
import esper
from components.ai_controller import AIController
from core.accessors import get_event_bus, get_audio_system
from events.attack_event import AttackEvent
from events.death_event import DeathEvent
from events.arrow_fired_event import ArrowFiredEvent
from events.fireball_fired_event import FireballFiredEvent
from components.base.team import Team
from components.gameplay.attack import Attack
from components.base.health import Health
from components.gameplay.target import Target
from components.base.position import Position
from core.ecs.iterator_system import IteratingProcessor
from components.base.cost import Cost
from enums.entity.entity_type import EntityType
from enums.sounds import origin, reasons


class CombatSystem(IteratingProcessor):
    """Handles combat between entities with attack and target components."""

    def __init__(self):
        super().__init__(Attack, Target, Position, Team)
        self.frame_count = 0
        get_event_bus().subscribe(AttackEvent, self.perform_attack)

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

        components = esper.components_for_entity(ent)

        if (
            esper.has_component(ent, AIController)
            and EntityType.GHAST not in components
        ):
            return

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
            for component in components:
                if (
                    isinstance(component, EntityType)
                    and component == EntityType.CROSSBOWMAN
                ):
                    get_event_bus().emit(ArrowFiredEvent(ent, pos, target_pos))
                    break

                # Fire fireball if attacker is a Ghast
                if isinstance(component, EntityType) and component == EntityType.GHAST:
                    get_event_bus().emit(FireballFiredEvent(ent, pos, target_pos))
                    break

            # Apply damage to target
            get_event_bus().emit(AttackEvent(ent, target.target_entity_id))

            attack.last_attack = self.frame_count

    def perform_attack(self, event: AttackEvent):
        """
        Perform attack from attacker to target, dealing damage and handling death.
        Emit a death event if the target's health reaches zero.

        Args:
            event: Attack event containing attacker and target IDs
        """
        attacker_id: int = event.fighter
        target_id: int = event.target
        if not esper.entity_exists(attacker_id) or not esper.entity_exists(target_id):
            return

        if not esper.has_component(attacker_id, Attack) or not esper.has_component(
            target_id, Health
        ):
            return

        atk: Attack = esper.component_for_entity(attacker_id, Attack)
        target_health: Health = esper.component_for_entity(target_id, Health)

        target_health.remaining = max(0, target_health.remaining - atk.damage)

        entity_type = esper.component_for_entity(target_id, EntityType)
        get_audio_system().play_sound(origin.ENTITY, entity_type, reasons.ATTACK)

        if target_health.remaining == 0:
            team = esper.component_for_entity(attacker_id, Team)
            cost_amount = 0
            if esper.has_component(target_id, Cost):
                cost_amount = (esper.component_for_entity(target_id, Cost)).amount

            get_event_bus().emit(DeathEvent(team, target_id, cost_amount))
