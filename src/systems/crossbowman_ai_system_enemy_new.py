"""
Simple AI System for Enemy CROSSBOWMAN Units (Team 2)

A streamlined AI system with pathfinding integration:
- Basic enemy detection and targeting
- A* pathfinding for intelligent movement
- Basic support for BRUTE allies
"""

import math
import esper
from components.ai import AIMemory, AIState, AIStateType, PathRequest
from components.attack import Attack
from components.health import Health
from components.position import Position
from components.target import Target
from components.team import Team
from components.velocity import Velocity
from enums.entity_type import EntityType


class CrossbowmanAISystemEnemy(esper.Processor):
    """
    AI System for CROSSBOWMAN units on team 2 with A* pathfinding.

    Key behaviors:
    - Find and attack enemies in range
    - Stay behind BRUTE allies when available
    - Smart movement with A* pathfinding
    """

    def __init__(self, targeting_system, pathfinding_system):
        """Initialize with targeting system and pathfinding system."""
        super().__init__()
        self.targeting_system = targeting_system
        self.pathfinding_system = pathfinding_system

    def process(self, dt):
        """Main AI processing with pathfinding integration."""
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
            if not esper.has_component(ent, PathRequest):
                esper.add_component(ent, PathRequest())

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

            # Smart AI logic with pathfinding
            self._smart_ai_behavior(ent, pos, attack, team.team_id)

    def _smart_ai_behavior(self, ent, pos, attack, team_id):
        """Main AI decision making with smart movement."""
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
            self._follow_brute_smart(ent, pos, ally_brute)

        else:
            # Nothing to do - move towards center intelligently
            self._move_to_center_smart(ent, pos)

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
            if distance <= attack.range * 24:  # Convert tiles to pixels
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
        """Attack an enemy with smart positioning."""
        enemy_id, enemy_pos, enemy_type = enemy_info
        distance = self._distance(pos, enemy_pos)

        # Set target for attacking
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(enemy_id))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = enemy_id

        # Position management with smart movement
        optimal_range = attack.range * 24 * 0.8  # 80% of max range in pixels

        if distance < optimal_range * 0.7:
            # Too close - back away smartly
            retreat_x = pos.x + (pos.x - enemy_pos.x) * 0.5
            retreat_y = pos.y + (pos.y - enemy_pos.y) * 0.5
            self._smart_move_to(ent, pos, retreat_x, retreat_y)
        elif distance > optimal_range:
            # Too far - get closer smartly
            self._smart_move_to(ent, pos, enemy_pos.x, enemy_pos.y)
        else:
            # Good distance - stop moving
            self._stop_movement(ent)

    def _follow_brute_smart(self, ent, pos, brute_info):
        """Follow an ally BRUTE using smart movement."""
        brute_id, brute_pos = brute_info
        follow_distance = 48  # 2 tiles behind

        # Position behind the BRUTE
        behind_x = brute_pos.x - 24
        behind_y = brute_pos.y

        distance = self._distance(pos, Position(behind_x, behind_y))

        if distance > follow_distance + 24:
            # Too far - get closer using smart movement
            self._smart_move_to(ent, pos, behind_x, behind_y)
        else:
            # Close enough - stop
            self._stop_movement(ent)

    def _move_to_center_smart(self, ent, pos):
        """Move towards the center using smart movement."""
        center_x = 12 * 24  # Center of 24x24 map
        center_y = 12 * 24

        self._smart_move_to(ent, pos, center_x, center_y)

    def _smart_move_to(self, ent, current_pos, target_x, target_y):
        """Smart movement using A* pathfinding when needed."""
        # Check if direct path is safe
        if self._is_direct_path_safe(current_pos, target_x, target_y):
            # Direct movement is safe
            self._move_towards_point(ent, current_pos, target_x, target_y)
        else:
            # Use A* pathfinding for complex navigation
            self._move_with_pathfinding(ent, current_pos, (target_x, target_y))

    def _is_direct_path_safe(self, start_pos, target_x, target_y):
        """Check if direct path is safe (no lava or major obstacles)."""
        # Sample points along the path
        steps = 8
        for i in range(1, steps):
            t = i / steps
            x = start_pos.x + t * (target_x - start_pos.x)
            y = start_pos.y + t * (target_y - start_pos.y)

            # Convert to grid coordinates
            grid_x = int(x // 24)
            grid_y = int(y // 24)

            # Check if this position has lava
            if hasattr(self.pathfinding_system, "terrain_map"):
                terrain = self.pathfinding_system.terrain_map.get(
                    (grid_x, grid_y), "UNKNOWN"
                )
                if terrain == "LAVA":
                    return False

        return True

    def _move_with_pathfinding(self, ent, current_pos, destination):
        """Use A* pathfinding for intelligent movement."""
        if not esper.has_component(ent, PathRequest):
            esper.add_component(ent, PathRequest())

        path_req = esper.component_for_entity(ent, PathRequest)

        # Request new path if needed
        if not path_req.path or path_req.destination != destination:
            path_req.destination = destination
            path_req.path = None
            path_req.current_index = 0
            print(f"[AI] Requesting A* path for CROSSBOWMAN {ent}")
            return

        # Follow existing path
        if path_req.path and path_req.current_index < len(path_req.path):
            waypoint = path_req.path[path_req.current_index]

            # Distance to current waypoint
            dx = waypoint.x - current_pos.x
            dy = waypoint.y - current_pos.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 25:  # Close to waypoint
                path_req.current_index += 1
                if path_req.current_index >= len(path_req.path):
                    # Path completed
                    print(f"[AI] CROSSBOWMAN {ent} reached destination via A*")
                    self._stop_movement(ent)
                    path_req.path = None
                    return

            # Move toward current waypoint
            if distance > 0:
                self._set_velocity(ent, (dx / distance) * 50, (dy / distance) * 50)
        else:
            # Fallback to direct movement if pathfinding fails
            print(f"[AI] CROSSBOWMAN {ent} using direct movement fallback")
            self._move_towards_point(ent, current_pos, destination[0], destination[1])

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
