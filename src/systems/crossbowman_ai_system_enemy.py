"""
Simple AI System for Enemy CROSSBOWMAN Units (Team 2)

A streamlined AI system with only essential behaviors:
- Basic enemy detection and targeting
- Simple movement towards/away from enemies
- Basic support for BRUTE allies
"""

import math
import esper
from components.ai import AIMemory, AIState, AIStateType
from components.attack import Attack
from components.health import Health
from components.position import Position
from components.target import Target
from components.team import Team
from components.velocity import Velocity
from enums.entity_type import EntityType


class CrossbowmanAISystemEnemy(esper.Processor):
    """
    Simplified AI System for CROSSBOWMAN units on team 2.

    Key behaviors:
    - Find and attack enemies in range
    - Stay behind BRUTE allies when available
    - Simple movement and positioning
    """

    def __init__(self, targeting_system):
        """Initialize with only the targeting system."""
        super().__init__()
        self.targeting_system = targeting_system

    def process(self, dt):
        """Main AI processing - simplified logic."""
        # Add AI components to team 2 CROSSBOWMAN units
        for ent, (team, entity_type, pos, attack, health) in esper.get_components(
            Team, EntityType, Position, Attack, Health
        ):
            if team.team_id != 2 or entity_type != EntityType.CROSSBOWMAN:
                continue

            # Add AI components if missing
            if not esper.has_component(ent, AIState):
                esper.add_component(ent, AIState())
                print(f"[AI] CROSSBOWMAN {ent} AI activated")
            if not esper.has_component(ent, AIMemory):
                esper.add_component(ent, AIMemory())

        # Process all units with AI
        for ent, (
            team,
            entity_type,
            pos,
            attack,
            health,
            ai_state,
        ) in esper.get_components(Team, EntityType, Position, Attack, Health, AIState):
            if team.team_id != 2 or entity_type != EntityType.CROSSBOWMAN:
                continue

            # Simple AI logic
            self._simple_ai_behavior(ent, pos, attack, team.team_id)

    def _simple_ai_behavior(self, ent, pos, attack, team_id):
        """Main AI decision making - very simple."""
        # 1. Look for enemies
        enemies = self._find_enemies_in_range(ent, pos, attack, team_id)

        # 2. Look for ally BRUTEs
        ally_brute = self._find_nearest_ally_brute(ent, pos, team_id)

        if enemies:
            # Enemies found - attack the closest one
            closest_enemy = min(enemies, key=lambda e: self._distance(pos, e[1]))
            self._attack_enemy(ent, pos, closest_enemy, attack)

        elif ally_brute:
            # No enemies but ally BRUTE exists - follow it
            self._follow_brute(ent, pos, ally_brute)

        else:
            # Nothing to do - move towards center
            self._move_to_center(ent, pos)

    def _find_enemies_in_range(self, ent, pos, attack, team_id):
        """Find all enemies within attack range."""
        enemies = []

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if target_ent == ent or target_team.team_id == team_id:
                continue

            # Must be alive
            if esper.has_component(target_ent, Health):
                target_health = esper.component_for_entity(target_ent, Health)
                if target_health.remaining <= 0:
                    continue

            # Check if in range
            distance = self._distance(pos, target_pos)
            if distance <= attack.range:
                enemies.append((target_ent, target_pos, target_type))

        return enemies

    def _find_nearest_ally_brute(self, ent, pos, team_id):
        """Find the nearest ally BRUTE."""
        closest_brute = None
        min_distance = float("inf")

        for brute_ent, (brute_team, brute_type, brute_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if (
                brute_ent == ent
                or brute_team.team_id != team_id
                or brute_type != EntityType.BRUTE
            ):
                continue

            distance = self._distance(pos, brute_pos)
            if distance < min_distance:
                min_distance = distance
                closest_brute = (brute_ent, brute_pos)

        return closest_brute

    def _attack_enemy(self, ent, pos, enemy_info, attack):
        """Attack an enemy - set target and position appropriately."""
        enemy_id, enemy_pos, enemy_type = enemy_info
        distance = self._distance(pos, enemy_pos)

        # Set target for attacking
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(enemy_id))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = enemy_id

        # Position management - keep optimal distance
        optimal_range = attack.range * 0.8

        if distance < optimal_range * 0.7:
            # Too close - back away
            self._move_away_from(ent, pos, enemy_pos)
        elif distance > optimal_range:
            # Too far - get closer
            self._move_towards(ent, pos, enemy_pos, optimal_range)
        else:
            # Good distance - stop moving
            self._stop_movement(ent)

    def _follow_brute(self, ent, pos, brute_info):
        """Follow an ally BRUTE at a safe distance."""
        brute_id, brute_pos = brute_info
        distance = self._distance(pos, brute_pos)

        follow_distance = 48  # 2 tiles behind

        if distance > follow_distance + 24:
            # Too far - get closer
            self._move_towards(ent, pos, brute_pos, follow_distance)
        else:
            # Close enough - stop
            self._stop_movement(ent)

    def _move_to_center(self, ent, pos):
        """Move towards the center of the map when idle."""
        center_x = 12 * 24  # Center of 24x24 map
        center_y = 12 * 24

        self._move_towards_point(ent, pos, center_x, center_y)

    def _move_towards(self, ent, pos, target_pos, desired_distance=0):
        """Move towards a target position, stopping at desired distance."""
        dx = target_pos.x - pos.x
        dy = target_pos.y - pos.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= desired_distance:
            self._stop_movement(ent)
            return

        # Normalize direction
        if distance > 0:
            dx = dx / distance
            dy = dy / distance

        # Set velocity
        self._set_velocity(ent, dx * 50, dy * 50)  # Speed of 50 pixels/frame

    def _move_towards_point(self, ent, pos, target_x, target_y):
        """Move towards a specific point."""
        dx = target_x - pos.x
        dy = target_y - pos.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 30:
            self._stop_movement(ent)
            return

        # Normalize and set velocity
        if distance > 0:
            dx = dx / distance * 50
            dy = dy / distance * 50

        self._set_velocity(ent, dx, dy)

    def _move_away_from(self, ent, pos, target_pos):
        """Move away from a target position."""
        dx = pos.x - target_pos.x
        dy = pos.y - target_pos.y
        distance = math.sqrt(dx * dx + dy * dy)

        # Normalize direction (away from target)
        if distance > 0:
            dx = dx / distance * 50
            dy = dy / distance * 50
        else:
            # If at same position, move in random direction
            dx, dy = 50, 0

        self._set_velocity(ent, dx, dy)

    def _set_velocity(self, ent, vx, vy):
        """Set entity velocity."""
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
        else:
            vel = Velocity(0, 0)
            esper.add_component(ent, vel)

        vel.x = vx
        vel.y = vy

    def _stop_movement(self, ent):
        """Stop entity movement."""
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
            vel.x = 0
            vel.y = 0

    def _distance(self, pos1, pos2):
        """Calculate distance between two positions."""
        return math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)
