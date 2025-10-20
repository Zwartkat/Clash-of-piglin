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
        # Debug: Count all units
        total_units = 0
        crossbowman_count = 0
        enemy_crossbowman_count = 0

        # Add AI components to team 2 CROSSBOWMAN units
        for ent, (team, entity_type, pos, attack, health) in esper.get_components(
            Team, EntityType, Position, Attack, Health
        ):
            total_units += 1

            if entity_type == EntityType.CROSSBOWMAN:
                crossbowman_count += 1
                print(
                    f"[AI DEBUG] Found CROSSBOWMAN {ent} on team {team.team_id} at ({pos.x:.1f}, {pos.y:.1f})"
                )

                if team.team_id == 2:  # Enemy team
                    enemy_crossbowman_count += 1

                    # Add AI components if missing
                    if not esper.has_component(ent, AIState):
                        esper.add_component(ent, AIState())
                        print(f"[AI DEBUG] Added AIState to CROSSBOWMAN {ent}")
                    if not esper.has_component(ent, AIMemory):
                        esper.add_component(ent, AIMemory())
                        print(f"[AI DEBUG] Added AIMemory to CROSSBOWMAN {ent}")
                    if not esper.has_component(ent, PathRequest):
                        esper.add_component(ent, PathRequest())
                        print(f"[AI DEBUG] Added PathRequest to CROSSBOWMAN {ent}")

        if total_units > 1:  # Skip if only map entity
            print(
                f"[AI DEBUG] Total: {total_units} units, CROSSBOWMAN: {crossbowman_count}, Enemy CROSSBOWMAN: {enemy_crossbowman_count}"
            )

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

            print(f"[AI DEBUG] Processing AI for CROSSBOWMAN {ent}")
            # Smart AI logic with pathfinding
            self._smart_ai_behavior(ent, pos, attack, team.team_id)

    def _smart_ai_behavior(self, ent, pos, attack, team_id):
        """Main AI decision making with smart movement and pathfinding.

        Decision hierarchy:
        0. If following an A* path -> Continue following path
        1. If enemies are in range -> Attack the closest enemy with optimal positioning
        2. If ally BRUTE exists -> Follow the BRUTE for support
        3. Otherwise -> Move to map center and wait for targets

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

        # Priority 1: Look for enemies
        enemies = self._find_enemies_in_range(ent, pos, attack, team_id)

        # Priority 2: Look for ally BRUTEs
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
            center_x = 12 * 32  # Center of 24x24 map with 32px tiles
            center_y = 12 * 32
            distance_to_center = self._distance(pos, Position(center_x, center_y))

            print(
                f"[AI DEBUG] Unit {ent} at ({pos.x:.1f}, {pos.y:.1f}), center: ({center_x}, {center_y}), distance: {distance_to_center:.1f}"
            )

            if distance_to_center > 25:  # Lower threshold to ensure movement
                print(
                    f"[AI DEBUG] Unit {ent} moving towards center (distance: {distance_to_center:.1f})"
                )
                self._move_to_center_smart(ent, pos)
            else:
                # Close to center - stop and wait
                print(
                    f"[AI DEBUG] Unit {ent} close to center, stopping (distance: {distance_to_center:.1f})"
                )
                self._stop_movement(ent)

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
            print(f"[AI DEBUG] Found {len(map_entities)} map entities")

            for map_entity, map_comp in map_entities:
                # IMPORTANT: esper returns a list containing the Map object!
                # We need to access the first element if it's a list
                if isinstance(map_comp, list) and len(map_comp) > 0:
                    actual_map = map_comp[0]  # Get the actual Map object
                    print(f"[AI DEBUG] Extracted Map from list: {type(actual_map)}")
                elif isinstance(map_comp, Map):
                    actual_map = map_comp
                    print(f"[AI DEBUG] Direct Map object: {type(actual_map)}")
                else:
                    print(
                        f"[AI DEBUG] Skipping unknown component type: {type(map_comp)}"
                    )
                    continue

                # Now we should have the actual Map object
                if not hasattr(actual_map, "tab") or not actual_map.tab:
                    print(f"[AI DEBUG] Map has no tab data")
                    continue

                terrain = actual_map.tab
                print(
                    f"[AI DEBUG] Found map with {len(terrain)}x{len(terrain[0])} terrain"
                )

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
                        print(
                            f"[AI DEBUG] Lava found at grid ({x},{y}) - path NOT safe"
                        )
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

                print(
                    f"[AI DEBUG] Path from grid ({start_x},{start_y}) to ({end_x},{end_y}) is safe"
                )
                return True

        except Exception as e:
            print(f"[AI DEBUG] Error in path safety check: {e}")
            import traceback

            traceback.print_exc()

        print(f"[AI DEBUG] No valid map data found - path assumed safe")
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
        print(
            f"[AI DEBUG] Unit {ent}: Path from ({current_pos.x},{current_pos.y}) to ({destination.x},{destination.y}) - Safe: {is_safe}"
        )

        if is_safe:
            # Direct path is safe - use simple movement
            print(f"[AI DEBUG] Unit {ent}: Using direct movement")
            self._move_towards_point(ent, current_pos, destination.x, destination.y)
        else:
            # Path blocked by obstacles - use A* pathfinding
            print(f"[AI DEBUG] Unit {ent}: Path blocked by lava, using A* pathfinding")
            self._request_pathfinding(ent, current_pos, destination)

    def _move_towards_point(self, ent, pos, target_x, target_y):
        """Move towards a specific point using the proper movement system."""
        # Ensure entity has a Velocity component
        if not esper.has_component(ent, Velocity):
            esper.add_component(ent, Velocity(x=0, y=0, speed=2))
            print(f"[AI DEBUG] Added Velocity component to unit {ent}")

        # Use the event system for proper movement
        print(
            f"[AI DEBUG] Unit {ent}: Sending EventMoveTo ({target_x:.1f}, {target_y:.1f})"
        )
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

        print(
            f"[AI DEBUG] Unit {ent}: Requested A* pathfinding to ({destination.x}, {destination.y})"
        )

    def _follow_astar_path(self, ent, pos, path_request):
        """Follow an A* calculated path.

        Returns:
            bool: True if still following path, False if path completed or invalid
        """
        if not path_request.path or len(path_request.path) == 0:
            return False  # No path to follow

        if path_request.current_index >= len(path_request.path):
            # Path completed
            print(f"[AI DEBUG] Unit {ent}: A* path completed")
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
            print(
                f"[AI DEBUG] Unit {ent}: Reached waypoint {path_request.current_index}/{len(path_request.path)}"
            )

            if path_request.current_index >= len(path_request.path):
                # Path completed
                print(f"[AI DEBUG] Unit {ent}: A* path completed")
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
