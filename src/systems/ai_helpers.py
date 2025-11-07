"""
AI Helper Classes for Crossbowman Unit System

This module contains helper classes that extract complex tactical behaviors
from the main AI system to improve code organization and maintainability.

Classes:
- BruteCoordination: Handles all BRUTE ally coordination logic
- BaseDefenseManager: Manages base defense strategies and positioning
- TargetPrioritizer: Handles enemy target selection and prioritization
- MovementController: Centralizes movement and positioning logic
"""

import math
import esper
from components.base.health import Health
from components.base.position import Position
from components.gameplay.target import Target
from components.base.team import Team
from enums.entity.entity_type import EntityType


class BruteCoordination:
    """
    Handles coordination between CROSSBOWMAN units and BRUTE allies.

    Manages BRUTE support distribution, combat coordination, and formation positioning.
    Ensures CROSSBOWMAN units never abandon BRUTE allies during combat.
    """

    def __init__(self, main_system):
        """Initialize with reference to main AI system for utility methods."""
        self.main = main_system

    def _move_closer_to_brute(self, unit_ent, unit_pos, brute_pos, distance_to_brute):
        """Move unit closer to BRUTE while maintaining tactical position."""
        direction_to_brute_x = brute_pos.x - unit_pos.x
        direction_to_brute_y = brute_pos.y - unit_pos.y
        brute_length = (direction_to_brute_x**2 + direction_to_brute_y**2) ** 0.5

        if brute_length > 0:
            move_distance = min(50, distance_to_brute - 100)
            direction_to_brute_x = direction_to_brute_x / brute_length * move_distance
            direction_to_brute_y = direction_to_brute_y / brute_length * move_distance

            new_x = unit_pos.x + direction_to_brute_x
            new_y = unit_pos.y + direction_to_brute_y

            # Clamp to map bounds
            new_x = max(32, min(new_x, 24 * 32 - 32))
            new_y = max(32, min(new_y, 24 * 32 - 32))

            destination = Position(new_x, new_y)
            self.main._smart_move_to(unit_ent, unit_pos, destination)

    def _adjust_range_to_enemy(
        self, unit_ent, unit_pos, enemy_pos, brute_pos, optimal_range
    ):
        """Adjust position to maintain optimal range to enemy while staying near BRUTE."""
        direction_to_enemy_x = enemy_pos.x - unit_pos.x
        direction_to_enemy_y = enemy_pos.y - unit_pos.y
        enemy_length = (direction_to_enemy_x**2 + direction_to_enemy_y**2) ** 0.5

        if enemy_length > 0:
            move_distance = min(
                30, self.main._distance(unit_pos, enemy_pos) - optimal_range
            )
            direction_to_enemy_x = direction_to_enemy_x / enemy_length * move_distance
            direction_to_enemy_y = direction_to_enemy_y / enemy_length * move_distance

            new_x = unit_pos.x + direction_to_enemy_x
            new_y = unit_pos.y + direction_to_enemy_y

            # Ensure we don't move too far from BRUTE
            test_distance_to_brute = self.main._distance(
                Position(new_x, new_y), brute_pos
            )
            if test_distance_to_brute <= 130:
                destination = Position(new_x, new_y)
                self.main._smart_move_to(unit_ent, unit_pos, destination)
            else:
                self.main._stop_movement(unit_ent)

    def find_brute_in_combat_nearby(self, unit_ent, unit_pos, team_id):
        """Find nearby BRUTE ally currently engaged in combat."""
        for brute_ent, (brute_pos, brute_team, brute_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if brute_team.team_id == team_id and brute_type == EntityType.BRUTE:
                distance_to_brute = self.main._distance(unit_pos, brute_pos)
                if (
                    distance_to_brute <= 120
                ):  # REDUCED from 200 to 120 - must be closer to detect combat
                    enemies_near_brute = self.main._count_nearby_enemies(
                        brute_pos, team_id, range_distance=120
                    )
                    if enemies_near_brute > 0:
                        return {
                            "entity": brute_ent,
                            "position": brute_pos,
                            "enemy_count": enemies_near_brute,
                        }
        return None

    def get_all_ally_brutes(self, team_id):
        """Get comprehensive information about all allied BRUTEs."""
        brutes = []
        for ent, (team, entity_type, pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if team.team_id == team_id and entity_type == EntityType.BRUTE:
                enemies_nearby = self.main._count_nearby_enemies(
                    pos, team_id, range_distance=120
                )
                brutes.append(
                    {
                        "entity": ent,
                        "position": pos,
                        "in_combat": enemies_nearby > 0,
                        "enemy_count": enemies_nearby,
                        "supporting_crossbowmen": 0,  # Calculated later
                    }
                )
        return brutes

    def find_brute_needing_support(self, ally_brutes, all_crossbowmen):
        """Determine which BRUTE most urgently needs crossbowman support."""
        total_crossbowmen = len(all_crossbowmen)
        total_brutes = len(ally_brutes)

        if total_brutes == 0:
            return None

        # Calculate support distribution
        ideal_support_per_brute = max(1, total_crossbowmen // total_brutes)

        # Priority 1: Combat BRUTEs with insufficient support
        combat_brutes_needing_help = []
        for brute in ally_brutes:
            if brute["in_combat"]:
                needed_support = min(brute["enemy_count"] + 1, 3)
                if brute["supporting_crossbowmen"] < needed_support:
                    urgency = (
                        needed_support - brute["supporting_crossbowmen"]
                    ) * 10 + brute["enemy_count"]
                    combat_brutes_needing_help.append((brute, urgency))

        if combat_brutes_needing_help:
            combat_brutes_needing_help.sort(key=lambda x: x[1], reverse=True)
            return combat_brutes_needing_help[0][0]

        # Priority 2: Unsupported BRUTEs
        unsupported_brutes = [
            b for b in ally_brutes if b["supporting_crossbowmen"] == 0
        ]
        if unsupported_brutes:
            return unsupported_brutes[0]

        # Priority 3: Under-supported BRUTEs
        under_supported = [
            b
            for b in ally_brutes
            if b["supporting_crossbowmen"] < ideal_support_per_brute
        ]
        if under_supported:
            return min(under_supported, key=lambda b: b["supporting_crossbowmen"])

        return None


class BaseDefenseManager:
    """
    Manages base defense strategies and positioning.

    Handles threat assessment, defender allocation, and defensive positioning
    to protect friendly BASTION from enemy attacks.
    """

    def __init__(self, main_system):
        """Initialize with reference to main AI system for utility methods."""
        self.main = main_system

    def is_base_under_attack(self, team_id):
        """Check if friendly base is currently under enemy attack."""
        base_pos = self.main._find_friendly_base(team_id)
        if not base_pos:
            return False

        enemies_near_base = self.count_enemies_attacking_base(team_id)
        return enemies_near_base > 0

    def count_enemies_attacking_base(self, team_id):
        """Count enemy units currently threatening the base."""
        base_pos = self.main._find_friendly_base(team_id)
        if not base_pos:
            return 0

        attackers = 0
        for ent, (enemy_pos, enemy_team, enemy_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if enemy_team.team_id != team_id and enemy_type != EntityType.BASTION:
                distance_to_base = self.main._distance(enemy_pos, base_pos)
                if distance_to_base <= 200:  # Attack range
                    attackers += 1

        return attackers

    def calculate_defenders_needed(self, attackers_count):
        """Calculate optimal number of defenders based on attacker count."""
        # Proportional defense: 1-2 attackers = 1 defender, 3-4 = 2, 5+ = 3 max
        if attackers_count <= 2:
            return 1
        elif attackers_count <= 4:
            return 2
        else:
            return 3

    def count_current_defenders(self, team_id):
        """Count allied units currently defending the base."""
        base_pos = self.main._find_friendly_base(team_id)
        if not base_pos:
            return 0

        defenders = 0
        for ent, (ally_pos, ally_team, ally_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ally_team.team_id == team_id and ally_type != EntityType.BASTION:
                distance_to_base = self.main._distance(ally_pos, base_pos)
                if distance_to_base <= 150:  # Defensive range
                    defenders += 1

        return defenders

    def find_base_threat(self, unit_pos, team_id):
        """Find the most threatening enemy near our base."""
        base_pos = self.main._find_friendly_base(team_id)
        if not base_pos:
            return None

        closest_threat = None
        min_distance = float("inf")

        for ent_enemy, (enemy_pos, enemy_team, enemy_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if enemy_team.team_id != team_id and enemy_type != EntityType.BASTION:
                # Check if alive
                if esper.has_component(ent_enemy, Health):
                    enemy_health = esper.component_for_entity(ent_enemy, Health)
                    if enemy_health.remaining <= 0:
                        continue

                distance_to_base = self.main._distance(enemy_pos, base_pos)
                distance_to_self = self.main._distance(unit_pos, enemy_pos)

                # Prioritize enemies threatening base
                if distance_to_base <= 250 and distance_to_self < min_distance:
                    min_distance = distance_to_self
                    closest_threat = (ent_enemy, enemy_pos, enemy_type)

        return closest_threat


class TargetPrioritizer:
    """
    Handles enemy target selection and prioritization.

    Implements intelligent target selection based on unit types, distances,
    and tactical situations to maximize combat effectiveness.
    """

    def __init__(self, main_system):
        """Initialize with reference to main AI system for utility methods."""
        self.main = main_system

    def prioritize_targets(self, enemies_in_range):
        """Select best target from available enemies based on priority."""
        if not enemies_in_range:
            return None

        # Separate by unit type for priority ordering
        ghasts = [e for e in enemies_in_range if e[2] == EntityType.GHAST]
        crossbowmen = [e for e in enemies_in_range if e[2] == EntityType.CROSSBOWMAN]
        brutes = [e for e in enemies_in_range if e[2] == EntityType.BRUTE]

        # Priority order: GHAST > CROSSBOWMAN > BRUTE
        if ghasts:
            return ghasts[0]
        elif crossbowmen:
            return crossbowmen[0]
        elif brutes:
            return brutes[0]
        else:
            return enemies_in_range[0]

    def calculate_brute_support_priority(
        self, target_type, distance_to_brute, distance_to_self
    ):
        """Calculate target priority specifically for BRUTE support scenarios."""
        base_priority = 0

        # Higher priority for dangerous enemies
        if target_type == EntityType.GHAST:
            base_priority = 150  # Extremely high - GHAST is deadly
        elif target_type == EntityType.CROSSBOWMAN:
            base_priority = 100  # High - ranged threat to BRUTE
        elif target_type == EntityType.BRUTE:
            base_priority = 80  # Medium-high - melee threat

        # Bonus for enemies very close to our BRUTE
        if distance_to_brute <= 80:
            base_priority += 50  # Immediate threat bonus
        elif distance_to_brute <= 120:
            base_priority += 30  # Close threat bonus

        # Small penalty for enemies far from us
        distance_penalty = min(distance_to_self / 20, 20)  # Capped penalty

        return base_priority - distance_penalty

    def find_closest_enemy_on_map(self, unit_ent, unit_pos, team_id):
        """Find the closest living enemy unit anywhere on the map."""
        closest_enemy = None
        min_distance = float("inf")

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if (
                target_ent == unit_ent
                or target_team.team_id == team_id
                or target_type == EntityType.BASTION
            ):
                continue

            # Must be alive
            if esper.has_component(target_ent, Health):
                target_health = esper.component_for_entity(target_ent, Health)
                if target_health.remaining <= 0:
                    continue

            distance = self.main._distance(unit_pos, target_pos)
            if distance < min_distance:
                min_distance = distance
                closest_enemy = (target_ent, target_pos, target_type)

        return closest_enemy

    def find_nearest_ghast(self, unit_pos, team_id, range_distance=400):
        """Find the nearest enemy GHAST that needs to be focused."""
        closest_ghast = None
        min_distance = float("inf")

        for ent, (ghast_pos, ghast_team, ghast_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ghast_team.team_id != team_id and ghast_type == EntityType.GHAST:
                distance = self.main._distance(unit_pos, ghast_pos)
                if distance <= range_distance and distance < min_distance:
                    min_distance = distance
                    closest_ghast = (ent, ghast_pos)

        return closest_ghast


class MovementController:
    """
    Centralizes movement and positioning logic for AI units.

    Handles positioning calculations, movement commands, and coordination
    between different tactical behaviors.
    """

    def __init__(self, main_system):
        """Initialize with reference to main AI system for utility methods."""
        self.main = main_system

    def position_for_brute_support(
        self, unit_ent, unit_pos, brute_pos, enemy_pos, attack
    ):
        """Calculate and execute optimal positioning to support BRUTE in combat."""
        optimal_range_to_enemy = attack.range * 24 * 0.85  # 85% of max range
        distance_to_enemy = self.main._distance(unit_pos, enemy_pos)
        distance_to_brute = self.main._distance(unit_pos, brute_pos)
        # Priority 1: Stay close to BRUTE (within 120 pixels)
        if distance_to_brute > 120:
            self._move_closer_to_brute(unit_ent, unit_pos, brute_pos, distance_to_brute)

        # Priority 2: Adjust range to enemy if close enough to BRUTE
        elif distance_to_enemy > optimal_range_to_enemy and distance_to_brute <= 120:
            self._adjust_range_to_enemy(
                unit_ent, unit_pos, enemy_pos, brute_pos, optimal_range_to_enemy
            )

        # Priority 3: Back away if too close to enemy
        elif (
            distance_to_enemy < optimal_range_to_enemy * 0.6
            and distance_to_brute <= 120
        ):
            self._retreat_from_enemy(unit_ent, unit_pos, enemy_pos, brute_pos)

        else:
            # Good position for BRUTE support
            self.main._stop_movement(unit_ent)

    def _move_closer_to_brute(self, unit_ent, unit_pos, brute_pos, distance_to_brute):
        """Move unit closer to BRUTE while maintaining tactical position."""
        direction_to_brute_x = brute_pos.x - unit_pos.x
        direction_to_brute_y = brute_pos.y - unit_pos.y
        brute_length = (direction_to_brute_x**2 + direction_to_brute_y**2) ** 0.5

        if brute_length > 0:
            move_distance = min(50, distance_to_brute - 100)
            direction_to_brute_x = direction_to_brute_x / brute_length * move_distance
            direction_to_brute_y = direction_to_brute_y / brute_length * move_distance

            new_x = unit_pos.x + direction_to_brute_x
            new_y = unit_pos.y + direction_to_brute_y

            # Clamp to map bounds
            new_x = max(32, min(new_x, 24 * 32 - 32))
            new_y = max(32, min(new_y, 24 * 32 - 32))

            destination = Position(new_x, new_y)
            self.main._smart_move_to(unit_ent, unit_pos, destination)

    def _adjust_range_to_enemy(
        self, unit_ent, unit_pos, enemy_pos, brute_pos, optimal_range
    ):
        """Adjust position to maintain optimal range to enemy while staying near BRUTE."""
        direction_to_enemy_x = enemy_pos.x - unit_pos.x
        direction_to_enemy_y = enemy_pos.y - unit_pos.y
        enemy_length = (direction_to_enemy_x**2 + direction_to_enemy_y**2) ** 0.5

        if enemy_length > 0:
            move_distance = min(
                30, self.main._distance(unit_pos, enemy_pos) - optimal_range
            )
            direction_to_enemy_x = direction_to_enemy_x / enemy_length * move_distance
            direction_to_enemy_y = direction_to_enemy_y / enemy_length * move_distance

            new_x = unit_pos.x + direction_to_enemy_x
            new_y = unit_pos.y + direction_to_enemy_y

            # Ensure we don't move too far from BRUTE
            test_distance_to_brute = self.main._distance(
                Position(new_x, new_y), brute_pos
            )
            if test_distance_to_brute <= 130:
                destination = Position(new_x, new_y)
                self.main._smart_move_to(unit_ent, unit_pos, destination)
            else:
                self.main._stop_movement(unit_ent)

    def _retreat_from_enemy(self, unit_ent, unit_pos, enemy_pos, brute_pos):
        """Retreat from enemy while maintaining proximity to BRUTE."""
        retreat_x = unit_pos.x + (unit_pos.x - enemy_pos.x) * 0.3
        retreat_y = unit_pos.y + (unit_pos.y - enemy_pos.y) * 0.3

        # Ensure retreat doesn't take us too far from BRUTE
        test_distance_to_brute = self.main._distance(
            Position(retreat_x, retreat_y), brute_pos
        )
        if test_distance_to_brute <= 130:
            # Clamp to map bounds
            retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
            retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

            destination = Position(retreat_x, retreat_y)
            self.main._smart_move_to(unit_ent, unit_pos, destination)
        else:
            # Can't retreat without leaving BRUTE - stay and fight
            self.main._stop_movement(unit_ent)

    def position_defensively_near_base(
        self, unit_ent, unit_pos, team_id, ideal_distance=120
    ):
        """Position unit defensively around the base at optimal distance."""
        base_pos = self.main._find_friendly_base(team_id)
        if not base_pos:
            # Fallback to team corner
            if team_id == 2:
                corner_x, corner_y = 20 * 32, 20 * 32
            else:
                corner_x, corner_y = 4 * 32, 4 * 32
            base_pos = Position(corner_x, corner_y)
        # Place the defender directly on the bastion position. The game logic
        # expects defenders to be near/at the bastion so they can immediately
        # intercept attackers; this avoids stacking in a corner.
        destination = Position(
            max(32, min(base_pos.x, 24 * 32 - 32)),
            max(32, min(base_pos.y, 24 * 32 - 32)),
        )
        self.main._smart_move_to(unit_ent, unit_pos, destination)

    def _move_to_defensive_perimeter(
        self, unit_ent, unit_pos, base_pos, ideal_distance
    ):
        """Move to a point on the defensive perimeter around the base.

        (Kept for backward compatibility; main code now uses circling behavior.)
        """
        # Fallback behavior: pick a perimeter point based on entity id
        angle = ((unit_ent * 53) % 360) * (math.pi / 180.0)
        defense_x = base_pos.x + math.cos(angle) * ideal_distance
        defense_y = base_pos.y + math.sin(angle) * ideal_distance

        # Clamp to map bounds
        defense_x = max(32, min(defense_x, 24 * 32 - 32))
        defense_y = max(32, min(defense_y, 24 * 32 - 32))

        destination = Position(defense_x, defense_y)
        self.main._smart_move_to(unit_ent, unit_pos, destination)
