"""
AI System for Enemy CROSSBOWMAN Units (Team 2)

This system controls CROSSBOWMAN units with intelligent pathfinding and tactical behavior:

Key Features:
- Terrain-aware pathfinding using A* algorithm to avoid lava and obstacles
- Optimal combat positioning at 80% of maximum attack range
- Formation support by following ally BRUTE units
- Smart target prioritization within attack range
- Fallback behavior when no targets or allies are available

Decision Hierarchy:
1. Attack enemies within range with optimal positioning
2. Follow ally BRUTE units for formation support
3. Move to map center and wait for opportunities

Technical Implementation:
- Uses ECS (Entity Component System) architecture with esper library
- Integrates with PathfindingSystem for A* navigation
- Maintains proper coordinate conversion between pixels and grid tiles
- Handles real-time pathfinding requests and waypoint following
"""

import math
import esper
from components.ai import AIMemory, AIState, AIStateType, PathRequest
from components.attack import Attack
from components.health import Health
from components.map import Map
from components.position import Position
from components.target import Target
from components.team import Team
from components.velocity import Velocity
from enums.case_type import CaseType
from enums.entity_type import EntityType
from core.event_bus import EventBus
from enums.unit_type import UnitType
from events.event_move import EventMoveTo


class CrossbowmanAISystemEnemy(esper.Processor):
    """
    AI system for CROSSBOWMAN units of team 2 with pathfinding integration.

    This simplified AI provides intelligent behaviors:
    - Move to center when idle
    - Follow allied BRUTE units for tactical coordination
    - Attack enemies within range with smart positioning
    - Use A* pathfinding to navigate around obstacles
    """

    def __init__(self, pathfinding_system):
        """
        Initialize the AI system.

        Args:
            pathfinding_system: Reference to the pathfinding system for terrain data
        """
        super().__init__()
        self.pathfinding_system = pathfinding_system
        # Load terrain data for obstacle detection
        self.terrain_map = getattr(pathfinding_system, "terrain_map", {})

    def process(self, dt):
        """Main AI processing with pathfinding integration."""
        # Add AI components to team 2 CROSSBOWMAN units
        for ent, (team, entity_type, pos, attack, health) in esper.get_components(
            Team, EntityType, Position, Attack, Health
        ):
            if (
                entity_type == EntityType.CROSSBOWMAN and team.team_id == 2
            ):  # Enemy team
                # Add AI components if missing
                if not esper.has_component(ent, AIState):
                    esper.add_component(ent, AIState())
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
        """Main AI decision making with advanced tactical behavior.

        New Tactical Logic:
        0. If following an A* path -> Continue following path
        1. If enemies in range -> Attack them
        2. Evaluate tactical situation:
           - If have BRUTE allies -> Attack with them (offensive)
           - If solo and outnumbered -> Retreat to base (defensive)
           - Otherwise -> Attack enemy base (aggressive)

        Args:
            ent: Entity ID
            pos (Position): Current unit position
            attack (Attack): Unit's attack component
            team_id (int): Team ID for friendly/enemy identification
        """
        # Priority 0: Follow A* pathfinding if active
        if esper.has_component(ent, PathRequest):
            path_request = esper.component_for_entity(ent, PathRequest)
            if self._follow_astar_path(ent, pos, path_request):
                return  # Still following path, skip other behaviors

        # Priority 1: Check for enemies in range
        enemies = self._find_enemies_in_range(ent, pos, attack, team_id)

        # Priority 2: If enemies found, decide how to handle them
        if enemies:
            # Check if we have BRUTE allies for coordination
            ally_brutes = self._count_ally_brutes(team_id)

            if ally_brutes > 0:
                # We have BRUTE allies - coordinate with them instead of attacking alone
                self._make_tactical_decision(ent, pos, attack, team_id)
                return
            else:
                # No BRUTE allies - attack directly
                closest_enemy = min(enemies, key=lambda e: self._distance(pos, e[1]))
                self._attack_enemy(ent, pos, closest_enemy, attack)
                return

        # Priority 3: No enemies in range - make tactical decision
        self._make_tactical_decision(ent, pos, attack, team_id)

    def _make_tactical_decision(self, ent, pos, attack, team_id):
        """Make tactical decisions based on battlefield situation."""
        # Analyze battlefield
        ally_brutes = self._count_ally_brutes(team_id)
        ally_crossbowmen = self._count_ally_crossbowmen(ent, team_id)
        nearby_enemies = self._count_nearby_enemies(pos, team_id, range_distance=200)

        # Decision 1: If we have BRUTE allies, fight with them
        if ally_brutes > 0:
            ally_brute_result = self._find_nearest_ally_brute(ent, pos, team_id)
            if ally_brute_result:
                brute_ent, brute_pos = ally_brute_result
                self._follow_brute_for_combat(ent, pos, brute_pos)
                return

        # Decision 2: If we're solo crossbowmen and outnumbered, retreat
        if ally_crossbowmen == 1 and ally_brutes == 0 and nearby_enemies >= 2:
            self._retreat_to_base(ent, pos, team_id)
            return

        # Decision 3: Otherwise, attack enemy base
        self._attack_enemy_base(ent, pos, team_id)

    def _find_enemies_in_range(self, ent, pos, attack, team_id):
        """Find all enemies within attack range for targeting.

        Scans all entities to identify hostile units within the crossbow's
        effective range. Used for target prioritization.

        Args:
            ent: Entity ID (self)
            pos (Position): Current unit position
            attack (Attack): Unit's attack component with range info
            team_id (int): Current unit's team ID

        Returns:
            list: List of (entity_id, position, entity_type) tuples for valid targets
        """
        enemies = []

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            # Skip self and allies (same team)
            if target_ent == ent or target_team.team_id == team_id:
                continue

            # ONLY target enemy team 1 (not neutral entities)
            if target_team.team_id != 1:
                continue

            # IGNORE BASTIONS - they are structures, not combat units!
            if target_type == EntityType.BASTION:
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
        """Find the nearest ally BRUTE for formation support.

        Locates the closest BRUTE ally to provide ranged support and
        follow in formation. CROSSBOWMAN units work best when supporting
        melee units like BRUTEs.

        Args:
            ent: Entity ID (self)
            pos (Position): Current unit position
            team_id (int): Current unit's team ID

        Returns:
            tuple or None: (brute_id, brute_position) of nearest ally BRUTE, or None if not found
        """
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
        """Attack an enemy with optimal positioning for crossbow combat.

        Maintains optimal combat distance (80% of max range) for effectiveness:
        - If too close: Retreats to avoid melee combat
        - If too far: Approaches to enter optimal range
        - If at good distance: Stops and focuses on targeting

        Args:
            ent: Entity ID
            pos (Position): Current unit position
            enemy_info (tuple): (enemy_id, enemy_pos, enemy_type)
            attack (Attack): Unit's attack component
        """
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
            # Too close - back away smartly (ensure coordinates stay in bounds)
            retreat_x = pos.x + (pos.x - enemy_pos.x) * 0.5
            retreat_y = pos.y + (pos.y - enemy_pos.y) * 0.5

            # Clamp coordinates to map bounds (24x24 tiles = 768x768 pixels)
            retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
            retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

            destination = Position(retreat_x, retreat_y)
            self._smart_move_to(ent, pos, destination)
        elif distance > optimal_range:
            # Too far - get closer smartly
            destination = Position(enemy_pos.x, enemy_pos.y)
            self._smart_move_to(ent, pos, destination)
        else:
            # Good distance - stop moving
            self._stop_movement(ent)

    def _follow_brute_smart(self, ent, pos, brute_info):
        """Follow an ally BRUTE using smart movement and positioning.

        Maintains a support formation behind the BRUTE to provide ranged support
        while staying out of melee combat range.

        Args:
            ent: Entity ID
            pos (Position): Current unit position
            brute_info (tuple): (brute_id, brute_pos) from ally BRUTE detection
        """
        brute_id, brute_pos = brute_info
        follow_distance = 48  # 2 tiles behind

        # Position behind the BRUTE (ensure coordinates stay within map bounds)
        behind_x = max(32, brute_pos.x - 24)  # Stay at least 1 tile from left edge
        behind_y = max(
            32, min(brute_pos.y, 24 * 32 - 32)
        )  # Stay within vertical bounds

        distance = self._distance(pos, Position(behind_x, behind_y))

        if distance > follow_distance + 24:
            # Too far - get closer using smart movement
            destination = Position(behind_x, behind_y)
            self._smart_move_to(ent, pos, destination)
        else:
            # Close enough - stop
            self._stop_movement(ent)

    def _count_ally_brutes(self, team_id):
        """Count allied BRUTE units."""
        count = 0
        for ent, (team, entity_type) in esper.get_components(Team, EntityType):
            if team.team_id == team_id and entity_type == EntityType.BRUTE:
                count += 1
        return count

    def _count_ally_crossbowmen(self, current_ent, team_id):
        """Count allied CROSSBOWMAN units (excluding self)."""
        count = 0
        for ent, (team, entity_type) in esper.get_components(Team, EntityType):
            if (
                ent != current_ent
                and team.team_id == team_id
                and entity_type == EntityType.CROSSBOWMAN
            ):
                count += 1
        return count + 1  # +1 for self

    def _count_nearby_enemies(self, pos, team_id, range_distance=200):
        """Count enemies within range."""
        count = 0
        for ent, (enemy_pos, enemy_team) in esper.get_components(Position, Team):
            if enemy_team.team_id != team_id:
                distance = self._distance(pos, enemy_pos)
                if distance <= range_distance:
                    count += 1
        return count

    def _follow_brute_for_combat(self, ent, pos, brute_pos):
        """Follow BRUTE ally for coordinated combat."""
        # Stay at optimal range behind BRUTE (support position)
        distance = self._distance(pos, brute_pos)
        if distance > 80:  # Too far from BRUTE
            self._smart_move_to(ent, pos, brute_pos)
        else:
            self._stop_movement(ent)

    def _retreat_to_base(self, ent, pos, team_id):
        """Retreat to friendly base."""
        # Find friendly base (BASTION of same team)
        base_pos = self._find_friendly_base(team_id)
        if base_pos:
            self._smart_move_to(ent, pos, base_pos)
        else:
            # Fallback: retreat to team spawn corner
            if team_id == 2:  # Team 2 spawns bottom-right
                corner_x, corner_y = 20 * 32, 20 * 32
            else:  # Team 1 spawns top-left
                corner_x, corner_y = 4 * 32, 4 * 32
            retreat_pos = Position(corner_x, corner_y)
            self._smart_move_to(ent, pos, retreat_pos)

    def _attack_enemy_base(self, ent, pos, team_id):
        """Attack enemy base."""
        enemy_team_id = 1 if team_id == 2 else 2
        enemy_base = self._find_enemy_base(enemy_team_id)

        if enemy_base:
            self._smart_move_to(ent, pos, enemy_base)
        else:
            # Fallback: attack enemy spawn corner
            if enemy_team_id == 1:  # Attack team 1 corner (top-left)
                corner_x, corner_y = 4 * 32, 4 * 32
            else:  # Attack team 2 corner (bottom-right)
                corner_x, corner_y = 20 * 32, 20 * 32
            attack_pos = Position(corner_x, corner_y)
            self._smart_move_to(ent, pos, attack_pos)

    def _find_friendly_base(self, team_id):
        """Find friendly BASTION."""
        for ent, (pos, team, entity_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if team.team_id == team_id and entity_type == EntityType.BASTION:
                return pos
        return None

    def _find_enemy_base(self, enemy_team_id):
        """Find enemy BASTION."""
        for ent, (pos, team, entity_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if team.team_id == enemy_team_id and entity_type == EntityType.BASTION:
                return pos
        return None

    def _move_to_center_smart(self, ent, pos):
        """Move towards the center using smart movement."""
        center_x = 12 * 32  # Center of 24x24 map in pixels
        center_y = 12 * 32

        destination = Position(center_x, center_y)
        self._smart_move_to(ent, pos, destination)

    def _is_direct_path_safe(self, current_pos, destination):
        """Check if direct path is safe without obstacles like lava.

        Args:
            current_pos (Position): Current unit position
            destination (Position): Target destination position

        Returns:
            bool: True if path is safe, False if blocked by obstacles
        """
        try:
            # Get map entities directly from esper
            map_entities = list(esper.get_components(Map))

            for map_entity, map_comp in map_entities:
                # IMPORTANT: esper returns a list containing the Map object!
                # We need to access the first element if it's a list
                if isinstance(map_comp, list) and len(map_comp) > 0:
                    actual_map = map_comp[0]  # Get the actual Map object
                elif isinstance(map_comp, Map):
                    actual_map = map_comp
                else:
                    continue

                # Now we should have the actual Map object
                if not hasattr(actual_map, "tab") or not actual_map.tab:
                    continue

                terrain = actual_map.tab

                # Convert world positions to grid coordinates
                CELL_SIZE = 32  # From config.yaml
                start_x = int(current_pos.x // CELL_SIZE)
                start_y = int(current_pos.y // CELL_SIZE)
                end_x = int(destination.x // CELL_SIZE)
                end_y = int(destination.y // CELL_SIZE)

                # Simple line check between start and end
                dx = abs(end_x - start_x)
                dy = abs(end_y - start_y)
                x, y = start_x, start_y
                x_inc = 1 if start_x < end_x else -1
                y_inc = 1 if start_y < end_y else -1
                error = dx - dy

                while True:
                    # Check bounds
                    if x < 0 or x >= len(terrain[0]) or y < 0 or y >= len(terrain):
                        break

                    # Check if current tile is lava
                    from enums.case_type import CaseType

                    case = terrain[y][x]  # Get the Case object
                    case_type = case.getType() if hasattr(case, "getType") else case

                    if case_type == CaseType.LAVA:
                        return False

                    if x == end_x and y == end_y:
                        break

                    e2 = 2 * error
                    if e2 > -dy:
                        error -= dy
                        x += x_inc
                    if e2 < dx:
                        error += dx
                        y += y_inc

                return True

        except Exception:
            pass

        return True

    def _smart_move_to(self, ent, current_pos, destination):
        """Enhanced movement with pathfinding when obstacles are detected.

        Decision process:
        1. Check if direct path is safe (no lava)
        2. If safe -> Use direct movement
        3. If blocked -> Request pathfinding from PathfindingSystem

        Args:
            ent: Entity ID
            current_pos (Position): Current unit position
            destination (Position): Target destination position
        """
        # Check if direct path is safe (no lava)
        is_safe = self._is_direct_path_safe(current_pos, destination)

        if is_safe:
            # Direct path is safe - use simple movement
            self._move_towards_point(ent, current_pos, destination.x, destination.y)
        else:
            # Path blocked by obstacles - use A* pathfinding
            self._request_pathfinding(ent, current_pos, destination)

    def _move_towards_point(self, ent, pos, target_x, target_y):
        """Move towards a specific point using the proper movement system."""
        # Ensure entity has a Velocity component
        if not esper.has_component(ent, Velocity):
            esper.add_component(ent, Velocity(x=0, y=0, speed=2))

        # Use the event system for proper movement
        EventBus.get_event_bus().emit(EventMoveTo(ent, target_x, target_y))

    def _request_pathfinding(self, ent, current_pos, destination):
        """Request A* pathfinding to navigate around obstacles."""
        # Add or update PathRequest component
        if not esper.has_component(ent, PathRequest):
            esper.add_component(ent, PathRequest())

        path_request = esper.component_for_entity(ent, PathRequest)
        path_request.destination = destination
        path_request.path = None  # Clear old path to trigger new calculation
        path_request.current_index = 0

    def _follow_astar_path(self, ent, pos, path_request):
        """Follow an A* calculated path.

        Returns:
            bool: True if still following path, False if path completed or invalid
        """
        if not path_request.path or len(path_request.path) == 0:
            return False  # No path to follow

        if path_request.current_index >= len(path_request.path):
            # Path completed
            path_request.path = None
            path_request.current_index = 0
            self._stop_movement(ent)
            return False

        # Get current waypoint
        waypoint = path_request.path[path_request.current_index]
        distance = self._distance(pos, waypoint)

        # Check if we've reached this waypoint
        if distance < 16:  # Close enough to waypoint
            path_request.current_index += 1

            if path_request.current_index >= len(path_request.path):
                # Path completed
                path_request.path = None
                path_request.current_index = 0
                self._stop_movement(ent)
                return False
            else:
                # Move to next waypoint
                next_waypoint = path_request.path[path_request.current_index]
                self._move_towards_point(ent, pos, next_waypoint.x, next_waypoint.y)
        else:
            # Still moving to current waypoint
            self._move_towards_point(ent, pos, waypoint.x, waypoint.y)

        return True  # Still following path

    def _stop_movement(self, ent):
        """Stop entity movement by setting velocity to zero."""
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
            vel.x = 0
            vel.y = 0

    def _distance(self, pos1, pos2):
        """Calculate distance between two positions."""
        return math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)
