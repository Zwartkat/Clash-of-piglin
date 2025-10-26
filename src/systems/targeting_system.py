import esper
from components.position import Position
from components.attack import Attack
from components.health import Health
from components.team import Team
from components.target import Target
from components.fly import Fly
from enums.entity_type import EntityType
from enums.unit_type import UnitType
from core.iterator_system import IteratingProcessor


class TargetingSystem(IteratingProcessor):
    """Finds and assigns enemy targets for attacking units."""

    attack_authorisation = {
        EntityType.GHAST: [EntityType.BASTION],
        EntityType.CROSSBOWMAN: [
            EntityType.CROSSBOWMAN,
            EntityType.BRUTE,
            EntityType.GHAST,
            EntityType.BASTION,
        ],
        EntityType.BRUTE: [
            EntityType.CROSSBOWMAN,
            EntityType.BRUTE,
            EntityType.BASTION,
        ],
        EntityType.BASTION: [],
    }

    def __init__(self):
        super().__init__(Position, Attack, Team)

    def process_entity(self, ent, dt, pos, attack, team):
        """
        Check current target and find new enemy if needed.

        Args:
            ent: Attacking entity ID
            dt: Time passed since last frame
            pos: Attacker position on map
            attack: Entity attack range and damage info
            team: Attacker team to avoid friendly fire
        """
        # Check if current target is still good
        current_target = None
        if esper.has_component(ent, Target):
            target_comp = esper.component_for_entity(ent, Target)
            if target_comp.target_entity_id and self._is_valid_target(
                target_comp.target_entity_id, ent, team.team_id, pos, attack
            ):
                current_target = target_comp.target_entity_id

        # Find new target if current one is lost
        if not current_target:
            new_target = self._find_closest_enemy(ent, pos, attack, team.team_id)

            if new_target:
                if esper.has_component(ent, Target):
                    target_comp = esper.component_for_entity(ent, Target)
                    target_comp.target_entity_id = new_target
                else:
                    esper.add_component(ent, Target(new_target))
            else:
                if esper.has_component(ent, Target):
                    target_comp = esper.component_for_entity(ent, Target)
                    target_comp.target_entity_id = None

    def _is_valid_target(
        self, target_id, attacker_id, attacker_team_id, attacker_pos, attack
    ):
        """
        Check if target is alive, enemy, and in range.

        Args:
            target_id: Target entity ID to check
            attacker_id: Attacker entity ID for type checking
            attacker_team_id: Attacker team to avoid friendly fire
            attacker_pos: Attacker position for range check
            attack: Attack component with range info

        Returns:
            bool: True if target is still valid to attack
        """
        if not esper.entity_exists(target_id):
            return False

        # Must be alive
        if esper.has_component(target_id, Health):
            health = esper.component_for_entity(target_id, Health)
            if health.remaining <= 0:
                return False
        else:
            return False

        # Must be enemy team
        if esper.has_component(target_id, Team):
            team = esper.component_for_entity(target_id, Team)
            if team.team_id == attacker_team_id:
                return False
        else:
            return False

        # Must be able to attack the target
        attacker_type = self._get_entity_type(attacker_id)
        target_type = self._get_entity_type(target_id)
        if not self._can_attack_target(attacker_type, target_type):
            return False

        # Must be in attack range
        if esper.has_component(target_id, Position):
            target_pos = esper.component_for_entity(target_id, Position)
            dx = target_pos.x - attacker_pos.x
            dy = target_pos.y - attacker_pos.y
            distance = (dx**2 + dy**2) ** 0.5
            if distance > attack.range:
                return False
        else:
            return False

        return True

    def _find_closest_enemy(self, attacker, attacker_pos, attack, attacker_team_id):
        """
        Find closest living enemy within attack range.

        Args:
            attacker: Attacker entity ID
            attacker_pos: Attacker position on map
            attack: Attack component with range info
            attacker_team_id: Attacker team to avoid friendly fire

        Returns:
            int: Closest enemy entity ID or None if no valid target
        """
        closest_enemy = None
        closest_distance = float("inf")
        attacker_type = self._get_entity_type(attacker)

        for target_ent, (target_pos, target_team) in esper.get_components(
            Position, Team
        ):
            # Skip allies and self
            if target_ent == attacker or target_team.team_id == attacker_team_id:
                continue

            # Must be alive
            if not esper.has_component(target_ent, Health):
                continue

            target_health = esper.component_for_entity(target_ent, Health)
            if target_health.remaining <= 0:
                continue

            # check if it can attack the target
            target_type = self._get_entity_type(target_ent)
            if not self._can_attack_target(attacker_type, target_type):
                # if attacker_type and target_type:
                #     print(
                #         f"DEBUG: {attacker_type.name if hasattr(attacker_type, 'name') else attacker_type} ne peut pas cibler {target_type.name if hasattr(target_type, 'name') else target_type}"
                #     )
                continue

                # Calculate distance
            dx = target_pos.x - attacker_pos.x
            dy = target_pos.y - attacker_pos.y
            distance = (dx**2 + dy**2) ** 0.5

            # Check if in range and closer than current best
            if distance <= attack.range and distance < closest_distance:
                closest_enemy = target_ent
                closest_distance = distance

        return closest_enemy

    def _get_entity_type(self, entity_id):
        """
        Détermine le type d'une entité en examinant ses composants.

        Args:
            entity_id: ID de l'entité

        Returns:
            EntityType: Type de l'entité ou None si non déterminé
        """

        try:
            components = esper.components_for_entity(entity_id)

            # search for the EntityType component
            for component in components:
                if isinstance(component, EntityType) and hasattr(
                    EntityType, component.name
                ):
                    return component

        except:
            pass
        return None

    def _can_attack_target(self, attacker_type, target_type):
        """
        Détermine si un type d'attaquant peut cibler un type d'ennemi.

        Args:
            attacker_type: EntityType de l'attaquant
            target_type: EntityType de la cible

        Returns:
            bool: True si l'attaquant peut cibler cette cible
        """
        if not attacker_type or not target_type:
            return True  # authorising the attack by default

        # check if the attacker can attack the target
        if attacker_type in self.attack_authorisation:
            if self.attack_authorisation[attacker_type] != []:
                return target_type in self.attack_authorisation[attacker_type]
            else:
                return False

        return True  # default return in case of error
