# src/systems/targeting_system.py
import esper
from components.position import Position
from components.attack import Attack
from components.health import Health
from components.team import Team
from components.target import Target
from core.iterator_system import IteratingProcessor


class TargetingSystem(IteratingProcessor):
    """Manages targeting of entities"""

    def __init__(self):
        super().__init__(Position, Attack, Team)

    def process_entity(self, ent, dt, pos, attack, team):
        # Check if current target is still valid
        current_target = None
        if esper.has_component(ent, Target):
            target_comp = esper.component_for_entity(ent, Target)
            if target_comp.target_entity_id and self._is_valid_target(
                target_comp.target_entity_id, team.team_id, pos, attack
            ):
                current_target = target_comp.target_entity_id

        # Find new target if needed
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

    def _is_valid_target(self, target_id, attacker_team_id, attacker_pos, attack):
        """Check if target is still valid"""
        if not esper.entity_exists(target_id):
            return False

        # Check health
        if esper.has_component(target_id, Health):
            health = esper.component_for_entity(target_id, Health)
            if health.remaining <= 0:
                return False
        else:
            return False

        # Check team
        if esper.has_component(target_id, Team):
            team = esper.component_for_entity(target_id, Team)
            if team.team_id == attacker_team_id:
                return False
        else:
            return False

        # Check range
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
        """Find closest enemy within attack range"""
        closest_enemy = None
        closest_distance = float("inf")

        for target_ent, (target_pos, target_team) in esper.get_components(
            Position, Team
        ):
            # Skip allies and self
            if target_ent == attacker or target_team.team_id == attacker_team_id:
                continue

            # Check health
            if not esper.has_component(target_ent, Health):
                continue

            target_health = esper.component_for_entity(target_ent, Health)
            if target_health.remaining <= 0:
                continue

            # Calculate distance
            dx = target_pos.x - attacker_pos.x
            dy = target_pos.y - attacker_pos.y
            distance = (dx**2 + dy**2) ** 0.5

            # Check if in range and closer
            if distance <= attack.range and distance < closest_distance:
                closest_enemy = target_ent
                closest_distance = distance

        return closest_enemy
