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
        """Make tactical decisions based on battlefield situation and force evaluation."""
        # ABSOLUTE PRIORITY: If there's a BRUTE ally nearby in combat, NEVER ABANDON THEM
        nearby_brute_in_combat = self._find_brute_in_combat_nearby(ent, pos, team_id)
        if nearby_brute_in_combat:
            # BRUTE is fighting nearby - STAY AND FIGHT, NO MATTER WHAT
            self._stay_and_fight_with_brute(
                ent, pos, attack, team_id, nearby_brute_in_combat
            )
            return

        # Analyze battlefield forces with point system
        ally_force = self._calculate_ally_force(ent, team_id, pos)
        enemy_force = self._calculate_enemy_force(team_id, pos, range_distance=300)

        # Priority 1: GHAST FOCUS - If there's a GHAST nearby, coordinate to kill it
        ghast_target = self._find_nearest_ghast(pos, team_id, range_distance=400)
        if ghast_target:
            self._handle_ghast_threat(
                ent, pos, attack, team_id, ghast_target, ally_force
            )
            return

        # Priority 2: BRUTE COORDINATION - If we have BRUTEs, coordinate with them intelligently
        ally_brutes = self._get_all_ally_brutes(team_id)
        if ally_brutes:
            # We have BRUTEs - use intelligent distribution system
            self._coordinate_brute_support(ent, pos, attack, team_id, ally_brutes)
            return

        # Priority 3: NO BRUTEs left - Evaluate force and decide strategy
        force_ratio = ally_force / max(enemy_force, 1)  # Avoid division by zero

        # Check if we're near our base for defensive considerations
        base_pos = self._find_friendly_base(team_id)
        near_base = False
        if base_pos:
            distance_to_base = self._distance(pos, base_pos)
            near_base = distance_to_base <= 150

        # Check if our base is under attack
        base_under_attack = self._is_base_under_attack(team_id)
        if base_under_attack:
            # Base is under attack - send proportional reinforcements
            attackers_count = self._count_enemies_attacking_base(team_id)
            defenders_needed = self._calculate_defenders_needed(
                team_id, attackers_count
            )
            current_defenders = self._count_current_base_defenders(team_id)

            if current_defenders < defenders_needed:
                # Need more defenders - go defend base
                self._defend_base_actively(ent, pos, team_id)
                return

        # IMPROVED: Better force evaluation and decision making
        if force_ratio < 0.5:  # Only retreat when clearly outnumbered (was 0.3)
            if near_base:
                self._defend_base_actively(ent, pos, team_id)
            else:
                self._tactical_retreat(ent, pos, team_id)
            return
        elif force_ratio >= 0.8 and force_ratio <= 1.2:  # Equal forces
            # Equal power - attack enemies first, then base
            self._attack_enemies_then_base(ent, pos, attack, team_id)
            return
        else:
            # Superior force - fight aggressively
            self._coordinated_group_attack(ent, pos, attack, team_id)
            return

    def _find_brute_in_combat_nearby(self, ent, pos, team_id):
        """Find if there's a BRUTE ally in combat within reasonable distance."""
        for brute_ent, (brute_pos, brute_team, brute_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if brute_team.team_id == team_id and brute_type == EntityType.BRUTE:
                distance_to_brute = self._distance(pos, brute_pos)
                if distance_to_brute <= 200:  # Within reasonable support distance
                    # Check if BRUTE is in combat
                    enemies_near_brute = self._count_nearby_enemies(
                        brute_pos, team_id, range_distance=120
                    )
                    if enemies_near_brute > 0:
                        return {
                            "entity": brute_ent,
                            "position": brute_pos,
                            "enemy_count": enemies_near_brute,
                        }
        return None

    def _stay_and_fight_with_brute(self, ent, pos, attack, team_id, brute_info):
        """NEVER ABANDON BRUTE IN COMBAT - Stay and fight no matter what."""
        brute_pos = brute_info["position"]
        brute_ent = brute_info["entity"]

        # Find enemies threatening the BRUTE and attack them
        priority_targets = []

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if target_team.team_id != team_id and target_type != EntityType.BASTION:
                # Check if alive
                if esper.has_component(target_ent, Health):
                    target_health = esper.component_for_entity(target_ent, Health)
                    if target_health.remaining <= 0:
                        continue

                distance_to_brute = self._distance(brute_pos, target_pos)
                distance_to_self = self._distance(pos, target_pos)

                # Target enemies that are threatening our BRUTE
                if (
                    distance_to_brute <= 150
                    and distance_to_self <= attack.range * 24 * 1.5
                ):  # Extended range for BRUTE support
                    priority = self._calculate_brute_support_priority(
                        target_type, distance_to_brute, distance_to_self
                    )
                    priority_targets.append(
                        (target_ent, target_pos, target_type, priority)
                    )

        if priority_targets:
            # Attack highest priority target threatening our BRUTE
            priority_targets.sort(key=lambda x: x[3], reverse=True)
            best_target = priority_targets[0]
            target_info = (best_target[0], best_target[1], best_target[2])

            # Set target for attacking
            if not esper.has_component(ent, Target):
                esper.add_component(ent, Target(best_target[0]))
            else:
                target_comp = esper.component_for_entity(ent, Target)
                target_comp.target_entity_id = best_target[0]

            # Position for optimal BRUTE support
            self._position_for_brute_support(
                ent, pos, brute_pos, target_info[1], attack
            )
        else:
            # No immediate threats, but stay close to BRUTE for support
            distance_to_brute = self._distance(pos, brute_pos)
            ideal_support_distance = 90  # Stay close for immediate support

            if distance_to_brute > ideal_support_distance + 30:
                # Get closer to BRUTE
                self._smart_move_to(ent, pos, brute_pos)
            elif distance_to_brute < ideal_support_distance - 20:
                # Maintain optimal distance
                direction_x = pos.x - brute_pos.x
                direction_y = pos.y - brute_pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    direction_x = direction_x / length * ideal_support_distance
                    direction_y = direction_y / length * ideal_support_distance

                    new_x = brute_pos.x + direction_x
                    new_y = brute_pos.y + direction_y

                    # Clamp to map bounds
                    new_x = max(32, min(new_x, 24 * 32 - 32))
                    new_y = max(32, min(new_y, 24 * 32 - 32))

                    destination = Position(new_x, new_y)
                    self._smart_move_to(ent, pos, destination)
            else:
                # Perfect support position - stop moving
                self._stop_movement(ent)

    def _calculate_brute_support_priority(
        self, target_type, distance_to_brute, distance_to_self
    ):
        """Calculate target priority specifically for BRUTE support."""
        base_priority = 0

        # Higher priority for dangerous enemies
        if target_type == EntityType.GHAST:
            base_priority = 150  # Extremely high priority - GHAST is deadly
        elif target_type == EntityType.CROSSBOWMAN:
            base_priority = 100  # High priority - ranged threats to BRUTE
        elif target_type == EntityType.BRUTE:
            base_priority = 80  # Medium-high priority - melee threat

        # Huge bonus for enemies very close to our BRUTE
        if distance_to_brute <= 80:
            base_priority += 50  # Immediate threat bonus
        elif distance_to_brute <= 120:
            base_priority += 30  # Close threat bonus

        # Small penalty for enemies far from us (but still prioritize BRUTE support)
        distance_penalty = min(distance_to_self / 20, 20)  # Cap penalty

        return base_priority - distance_penalty

    def _position_for_brute_support(self, ent, pos, brute_pos, enemy_pos, attack):
        """Position optimally to support BRUTE in combat."""
        # Calculate ideal position: Close enough to BRUTE for support, optimal range for enemy
        optimal_range_to_enemy = attack.range * 24 * 0.85  # 85% of max range
        distance_to_enemy = self._distance(pos, enemy_pos)
        distance_to_brute = self._distance(pos, brute_pos)

        # Priority 1: Stay close to BRUTE (within 120 pixels)
        if distance_to_brute > 120:
            # Too far from BRUTE - get closer while maintaining shooting position
            # Calculate position between BRUTE and enemy that keeps us close to BRUTE
            direction_to_brute_x = brute_pos.x - pos.x
            direction_to_brute_y = brute_pos.y - pos.y
            brute_length = (direction_to_brute_x**2 + direction_to_brute_y**2) ** 0.5

            if brute_length > 0:
                # Move 60% towards BRUTE
                move_distance = min(50, distance_to_brute - 100)
                direction_to_brute_x = (
                    direction_to_brute_x / brute_length * move_distance
                )
                direction_to_brute_y = (
                    direction_to_brute_y / brute_length * move_distance
                )

                new_x = pos.x + direction_to_brute_x
                new_y = pos.y + direction_to_brute_y

                # Clamp to map bounds
                new_x = max(32, min(new_x, 24 * 32 - 32))
                new_y = max(32, min(new_y, 24 * 32 - 32))

                destination = Position(new_x, new_y)
                self._smart_move_to(ent, pos, destination)

        # Priority 2: Adjust range to enemy if we're close enough to BRUTE
        elif distance_to_enemy > optimal_range_to_enemy and distance_to_brute <= 120:
            # Get closer to enemy while staying near BRUTE
            direction_to_enemy_x = enemy_pos.x - pos.x
            direction_to_enemy_y = enemy_pos.y - pos.y
            enemy_length = (direction_to_enemy_x**2 + direction_to_enemy_y**2) ** 0.5

            if enemy_length > 0:
                move_distance = min(30, distance_to_enemy - optimal_range_to_enemy)
                direction_to_enemy_x = (
                    direction_to_enemy_x / enemy_length * move_distance
                )
                direction_to_enemy_y = (
                    direction_to_enemy_y / enemy_length * move_distance
                )

                new_x = pos.x + direction_to_enemy_x
                new_y = pos.y + direction_to_enemy_y

                # Make sure we don't move too far from BRUTE
                test_distance_to_brute = self._distance(
                    Position(new_x, new_y), brute_pos
                )
                if test_distance_to_brute <= 130:  # Allow slight margin
                    destination = Position(new_x, new_y)
                    self._smart_move_to(ent, pos, destination)
                else:
                    # Stay put if moving would take us too far from BRUTE
                    self._stop_movement(ent)

        elif (
            distance_to_enemy < optimal_range_to_enemy * 0.6
            and distance_to_brute <= 120
        ):
            # Too close to enemy - back away slightly but stay near BRUTE
            retreat_x = pos.x + (pos.x - enemy_pos.x) * 0.3
            retreat_y = pos.y + (pos.y - enemy_pos.y) * 0.3

            # Make sure retreat doesn't take us too far from BRUTE
            test_distance_to_brute = self._distance(
                Position(retreat_x, retreat_y), brute_pos
            )
            if test_distance_to_brute <= 130:
                # Clamp to map bounds
                retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
                retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

                destination = Position(retreat_x, retreat_y)
                self._smart_move_to(ent, pos, destination)
            else:
                # Can't retreat without leaving BRUTE - stay and fight
                self._stop_movement(ent)
        else:
            # Good position for BRUTE support - hold position and fight
            self._stop_movement(ent)

    def _is_base_under_attack(self, team_id):
        """Check if our base is currently under attack."""
        base_pos = self._find_friendly_base(team_id)
        if not base_pos:
            return False

        # Check for enemies near base
        enemies_near_base = self._count_enemies_attacking_base(team_id)
        return enemies_near_base > 0

    def _count_enemies_attacking_base(self, team_id):
        """Count enemies currently attacking our base."""
        base_pos = self._find_friendly_base(team_id)
        if not base_pos:
            return 0

        attackers = 0
        for ent, (enemy_pos, enemy_team, enemy_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if enemy_team.team_id != team_id and enemy_type != EntityType.BASTION:
                distance_to_base = self._distance(enemy_pos, base_pos)
                if distance_to_base <= 200:  # Within attack range of base
                    attackers += 1

        return attackers

    def _calculate_defenders_needed(self, team_id, attackers_count):
        """Calculate how many defenders we need based on attackers."""
        # Rule: need proportional defenders
        # 1-2 attackers = 1 defender
        # 3-4 attackers = 2 defenders
        # 5+ attackers = 3 defenders (max)
        if attackers_count <= 2:
            return 1
        elif attackers_count <= 4:
            return 2
        else:
            return 3

    def _count_current_base_defenders(self, team_id):
        """Count allies currently defending the base."""
        base_pos = self._find_friendly_base(team_id)
        if not base_pos:
            return 0

        defenders = 0
        for ent, (ally_pos, ally_team, ally_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ally_team.team_id == team_id and ally_type != EntityType.BASTION:
                distance_to_base = self._distance(ally_pos, base_pos)
                if distance_to_base <= 150:  # Within defensive range
                    defenders += 1

        return defenders

    def _defend_base_actively(self, ent, pos, team_id):
        """Actively defend the base with aggressive engagement."""
        base_pos = self._find_friendly_base(team_id)
        if not base_pos:
            # No base found, fallback to corner defense
            if team_id == 2:
                corner_x, corner_y = 20 * 32, 20 * 32
            else:
                corner_x, corner_y = 4 * 32, 4 * 32
            base_pos = Position(corner_x, corner_y)

        # Find closest enemy threatening the base
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

                distance_to_base = self._distance(enemy_pos, base_pos)
                distance_to_self = self._distance(pos, enemy_pos)

                # Prioritize enemies threatening base within reasonable range
                if distance_to_base <= 250 and distance_to_self < min_distance:
                    min_distance = distance_to_self
                    closest_threat = (ent_enemy, enemy_pos, enemy_type)

        if closest_threat:
            # Attack the threat while maintaining defensive position
            enemy_ent, enemy_pos, enemy_type = closest_threat

            # Set target
            if not esper.has_component(ent, Target):
                esper.add_component(ent, Target(enemy_ent))
            else:
                target_comp = esper.component_for_entity(ent, Target)
                target_comp.target_entity_id = enemy_ent

            # Position aggressively but don't stray too far from base
            distance_to_enemy = self._distance(pos, enemy_pos)
            distance_to_base = self._distance(pos, base_pos)
            optimal_range = 100  # Aggressive defensive range

            if distance_to_enemy > optimal_range and distance_to_base <= 200:
                # Get closer to enemy if we're not too far from base
                direction_x = enemy_pos.x - pos.x
                direction_y = enemy_pos.y - pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    move_distance = min(40, distance_to_enemy - optimal_range)
                    direction_x = direction_x / length * move_distance
                    direction_y = direction_y / length * move_distance

                    new_x = pos.x + direction_x
                    new_y = pos.y + direction_y

                    # Ensure we don't move too far from base
                    test_distance_to_base = self._distance(
                        Position(new_x, new_y), base_pos
                    )
                    if test_distance_to_base <= 200:
                        destination = Position(new_x, new_y)
                        self._smart_move_to(ent, pos, destination)
                    else:
                        self._stop_movement(ent)
            elif distance_to_enemy < optimal_range * 0.6:
                # Too close - back away toward base
                retreat_x = pos.x + (base_pos.x - enemy_pos.x) * 0.3
                retreat_y = pos.y + (base_pos.y - enemy_pos.y) * 0.3

                # Clamp to map bounds
                retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
                retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

                destination = Position(retreat_x, retreat_y)
                self._smart_move_to(ent, pos, destination)
            else:
                # Good position for active defense
                self._stop_movement(ent)
        else:
            # No immediate threats - position defensively around base
            distance_to_base = self._distance(pos, base_pos)
            ideal_defense_distance = 120  # Closer defensive positioning

            if distance_to_base > ideal_defense_distance + 40:
                # Too far from base, move closer
                self._smart_move_to(ent, pos, base_pos)
            elif distance_to_base < ideal_defense_distance - 20:
                # Too close to base, move to better defensive position
                direction_x = pos.x - base_pos.x
                direction_y = pos.y - base_pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    direction_x = direction_x / length * ideal_defense_distance
                    direction_y = direction_y / length * ideal_defense_distance

                    defense_x = base_pos.x + direction_x
                    defense_y = base_pos.y + direction_y

                    # Clamp to map bounds
                    defense_x = max(32, min(defense_x, 24 * 32 - 32))
                    defense_y = max(32, min(defense_y, 24 * 32 - 32))

                    destination = Position(defense_x, defense_y)
                    self._smart_move_to(ent, pos, destination)
            else:
                # Good defensive position - patrol/watch
                self._stop_movement(ent)

    def _attack_enemies_then_base(self, ent, pos, attack, team_id):
        """Attack enemies first, then attack enemy base - for equal power situations."""
        # First priority: attack any enemies in range
        enemies_in_range = self._find_enemies_in_range(ent, pos, attack, team_id)

        if enemies_in_range:
            # Enemies found - attack them first
            best_target = self._prioritize_targets(enemies_in_range)
            self._attack_enemy(ent, pos, best_target, attack)
        else:
            # No enemies in range - look for enemies on the map
            closest_enemy = self._find_closest_enemy_on_map(ent, pos, team_id)

            if closest_enemy:
                # Move toward closest enemy
                enemy_ent, enemy_pos, enemy_type = closest_enemy
                distance_to_enemy = self._distance(pos, enemy_pos)

                if (
                    distance_to_enemy <= attack.range * 24 * 1.2
                ):  # Within extended range
                    # Close enough to engage
                    self._attack_enemy(ent, pos, closest_enemy, attack)
                else:
                    # Move closer to enemy
                    self._smart_move_to(ent, pos, enemy_pos)
            else:
                # No enemies left - attack enemy base
                self._attack_enemy_base(ent, pos, team_id)

    def _find_closest_enemy_on_map(self, ent, pos, team_id):
        """Find the closest enemy unit anywhere on the map."""
        closest_enemy = None
        min_distance = float("inf")

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if (
                target_ent == ent
                or target_team.team_id == team_id
                or target_type == EntityType.BASTION
            ):
                continue

            # Must be alive
            if esper.has_component(target_ent, Health):
                target_health = esper.component_for_entity(target_ent, Health)
                if target_health.remaining <= 0:
                    continue

            distance = self._distance(pos, target_pos)
            if distance < min_distance:
                min_distance = distance
                closest_enemy = (target_ent, target_pos, target_type)

        return closest_enemy

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

    def _get_all_ally_brutes(self, team_id):
        """Get all ally BRUTEs with their positions and combat status."""
        brutes = []
        for ent, (team, entity_type, pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if team.team_id == team_id and entity_type == EntityType.BRUTE:
                # Check if BRUTE is in combat
                enemies_nearby = self._count_nearby_enemies(
                    pos, team_id, range_distance=120
                )
                brutes.append(
                    {
                        "entity": ent,
                        "position": pos,
                        "in_combat": enemies_nearby > 0,
                        "enemy_count": enemies_nearby,
                        "supporting_crossbowmen": 0,  # Will be calculated
                    }
                )
        return brutes

    def _coordinate_brute_support(self, ent, pos, attack, team_id, ally_brutes):
        """Intelligent coordination system for BRUTE support.

        Strategy:
        1. Analyze all BRUTEs and their needs
        2. Count current crossbowmen supporting each BRUTE
        3. Assign this crossbowman to the BRUTE that needs support most
        4. Stay with assigned BRUTE and fight alongside them
        """
        # Get all crossbowmen positions for distribution analysis
        all_crossbowmen = []
        for crossbow_ent, (team, entity_type, crossbow_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if team.team_id == team_id and entity_type == EntityType.CROSSBOWMAN:
                all_crossbowmen.append(
                    {"entity": crossbow_ent, "position": crossbow_pos}
                )

        # Calculate current support for each BRUTE
        for brute in ally_brutes:
            support_count = 0
            for crossbow in all_crossbowmen:
                distance = self._distance(crossbow["position"], brute["position"])
                if distance <= 150:  # Consider as "supporting" if within 150 pixels
                    support_count += 1
            brute["supporting_crossbowmen"] = support_count

        # Find the BRUTE that needs support most
        best_brute = self._find_brute_needing_support(ally_brutes, all_crossbowmen)

        if best_brute:
            # Assign this crossbowman to support the selected BRUTE
            self._provide_dedicated_brute_support(ent, pos, attack, team_id, best_brute)
        else:
            # Fallback: support nearest BRUTE
            nearest_brute = min(
                ally_brutes, key=lambda b: self._distance(pos, b["position"])
            )
            self._provide_dedicated_brute_support(
                ent, pos, attack, team_id, nearest_brute
            )

    def _find_brute_needing_support(self, ally_brutes, all_crossbowmen):
        """Find which BRUTE needs crossbowman support most urgently.

        Priority:
        1. BRUTEs in combat with too few supporters
        2. BRUTEs facing multiple enemies
        3. BRUTEs with no support at all
        """
        # Calculate ideal support ratio
        total_crossbowmen = len(all_crossbowmen)
        total_brutes = len(ally_brutes)

        if total_brutes == 0:
            return None

        ideal_support_per_brute = max(1, total_crossbowmen // total_brutes)

        # Priority 1: BRUTEs in combat with insufficient support
        combat_brutes_needing_help = []
        for brute in ally_brutes:
            if brute["in_combat"]:
                needed_support = min(
                    brute["enemy_count"] + 1, 3
                )  # Max 3 crossbowmen per BRUTE
                if brute["supporting_crossbowmen"] < needed_support:
                    urgency = (
                        needed_support - brute["supporting_crossbowmen"]
                    ) * 10 + brute["enemy_count"]
                    combat_brutes_needing_help.append((brute, urgency))

        if combat_brutes_needing_help:
            # Return BRUTE with highest urgency
            combat_brutes_needing_help.sort(key=lambda x: x[1], reverse=True)
            return combat_brutes_needing_help[0][0]

        # Priority 2: BRUTEs with no support at all
        unsupported_brutes = [
            b for b in ally_brutes if b["supporting_crossbowmen"] == 0
        ]
        if unsupported_brutes:
            # Return first unsupported BRUTE
            return unsupported_brutes[0]

        # Priority 3: Balance support across all BRUTEs
        underSupported_brutes = [
            b
            for b in ally_brutes
            if b["supporting_crossbowmen"] < ideal_support_per_brute
        ]
        if underSupported_brutes:
            return min(underSupported_brutes, key=lambda b: b["supporting_crossbowmen"])

        return None  # All BRUTEs have adequate support

    def _provide_dedicated_brute_support(self, ent, pos, attack, team_id, brute_info):
        """Provide dedicated support to a specific BRUTE - NEVER ABANDON THEM IN COMBAT."""
        brute_pos = brute_info["position"]
        brute_ent = brute_info["entity"]
        in_combat = brute_info["in_combat"]

        if in_combat:
            # BRUTE is fighting - ABSOLUTE PRIORITY: STAY AND FIGHT WITH BRUTE
            # Never retreat, never abandon, always support
            self._stay_and_fight_with_brute(ent, pos, attack, team_id, brute_info)
        else:
            # BRUTE is moving - follow in formation but stay close for immediate combat support
            distance_to_brute = self._distance(pos, brute_pos)
            optimal_follow_distance = 80  # Stay closer for immediate combat response

            if distance_to_brute > optimal_follow_distance + 30:
                # Too far - get closer quickly
                self._smart_move_to(ent, pos, brute_pos)
            elif distance_to_brute < optimal_follow_distance - 20:
                # Too close - maintain proper distance for ranged support
                direction_x = pos.x - brute_pos.x
                direction_y = pos.y - brute_pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    direction_x = direction_x / length * optimal_follow_distance
                    direction_y = direction_y / length * optimal_follow_distance

                    new_x = brute_pos.x + direction_x
                    new_y = brute_pos.y + direction_y

                    # Clamp to map bounds
                    new_x = max(32, min(new_x, 24 * 32 - 32))
                    new_y = max(32, min(new_y, 24 * 32 - 32))

                    destination = Position(new_x, new_y)
                    self._smart_move_to(ent, pos, destination)
            else:
                # Perfect formation distance - ready for immediate combat support
                self._stop_movement(ent)

    def _active_combat_support(self, ent, pos, attack, team_id, brute_pos):
        """Provide active combat support to fighting BRUTE."""
        # Find enemies threatening the BRUTE
        priority_targets = []

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if target_team.team_id != team_id and target_type != EntityType.BASTION:
                distance_to_brute = self._distance(brute_pos, target_pos)
                distance_to_self = self._distance(pos, target_pos)

                # Target enemies that are threatening our BRUTE
                if (
                    distance_to_brute <= 120
                    and distance_to_self <= attack.range * 24 * 1.3
                ):
                    priority = self._calculate_target_priority(
                        target_type, distance_to_brute, distance_to_self
                    )
                    priority_targets.append(
                        (target_ent, target_pos, target_type, priority)
                    )

        if priority_targets:
            # Attack highest priority target
            priority_targets.sort(key=lambda x: x[3], reverse=True)
            best_target = priority_targets[0]
            target_info = (best_target[0], best_target[1], best_target[2])

            # Engage target while maintaining support position
            self._attack_enemy(ent, pos, target_info, attack)
        else:
            # No immediate threats, maintain support position near BRUTE
            distance_to_brute = self._distance(pos, brute_pos)
            ideal_support_distance = 80

            if distance_to_brute > ideal_support_distance + 20:
                # Get closer to BRUTE
                direction_x = brute_pos.x - pos.x
                direction_y = brute_pos.y - pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    move_distance = min(30, distance_to_brute - ideal_support_distance)
                    direction_x = direction_x / length * move_distance
                    direction_y = direction_y / length * move_distance

                    new_x = pos.x + direction_x
                    new_y = pos.y + direction_y

                    # Clamp to map bounds
                    new_x = max(32, min(new_x, 24 * 32 - 32))
                    new_y = max(32, min(new_y, 24 * 32 - 32))

                    destination = Position(new_x, new_y)
                    self._smart_move_to(ent, pos, destination)
            else:
                # Good support position
                self._stop_movement(ent)

    def _calculate_target_priority(
        self, target_type, distance_to_brute, distance_to_self
    ):
        """Calculate target priority for BRUTE support."""
        base_priority = 0

        # Base priority by unit type
        if target_type == EntityType.GHAST:
            base_priority = 100  # Highest priority
        elif target_type == EntityType.CROSSBOWMAN:
            base_priority = 80  # High priority (ranged threat)
        elif target_type == EntityType.BRUTE:
            base_priority = 60  # Medium priority

        # Bonus for enemies close to our BRUTE
        distance_bonus = max(0, 120 - distance_to_brute)

        # Penalty for enemies far from us
        distance_penalty = distance_to_self / 10

        return base_priority + distance_bonus - distance_penalty

    def _coordinated_group_attack(self, ent, pos, attack, team_id):
        """Coordinated group attack when no BRUTEs left but force is superior."""
        # Prioritize targets: Enemy base > Enemy groups > Individual enemies

        # First, try to attack enemy base
        enemy_team_id = 1 if team_id == 2 else 2
        enemy_base = self._find_enemy_base(enemy_team_id)

        if enemy_base:
            # Check if other crossbowmen are also attacking the base
            crossbowmen_near_base = 0
            for crossbow_ent, (team, entity_type, crossbow_pos) in esper.get_components(
                Team, EntityType, Position
            ):
                if (
                    team.team_id == team_id
                    and entity_type == EntityType.CROSSBOWMAN
                    and crossbow_ent != ent
                ):
                    distance_to_base = self._distance(crossbow_pos, enemy_base)
                    if distance_to_base <= 200:  # Others are attacking base
                        crossbowmen_near_base += 1

            # Join the base attack if others are doing it, or start it
            if crossbowmen_near_base > 0 or self._distance(pos, enemy_base) <= 300:
                self._smart_move_to(ent, pos, enemy_base)
                return

        # Fallback: Look for enemy groups to attack
        enemies_in_range = self._find_enemies_in_range(ent, pos, attack, team_id)
        if enemies_in_range:
            best_target = self._prioritize_targets(enemies_in_range)
            self._attack_enemy(ent, pos, best_target, attack)
        else:
            # Move towards enemy territory to find targets
            if enemy_base:
                self._smart_move_to(ent, pos, enemy_base)
            else:
                # Fallback: move to enemy spawn area
                if enemy_team_id == 1:
                    target_pos = Position(4 * 32, 4 * 32)  # Top-left
                else:
                    target_pos = Position(20 * 32, 20 * 32)  # Bottom-right
                self._smart_move_to(ent, pos, target_pos)

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

    def _calculate_ally_force(self, current_ent, team_id, pos, range_distance=400):
        """Calculate total ally force using point system.
        BRUTE = 3 points, CROSSBOWMAN = 5 points, GHAST = 8 points
        """
        total_force = 0

        for ent, (ally_pos, ally_team, ally_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ally_team.team_id == team_id:
                # Check if ally is in reasonable range to help
                distance = self._distance(pos, ally_pos)
                if distance <= range_distance:
                    if ally_type == EntityType.BRUTE:
                        total_force += 3
                    elif ally_type == EntityType.CROSSBOWMAN:
                        total_force += 5
                    elif ally_type == EntityType.GHAST:
                        total_force += 8

        return total_force

    def _calculate_enemy_force(self, team_id, pos, range_distance=300):
        """Calculate total enemy force in range using point system."""
        total_force = 0

        for ent, (enemy_pos, enemy_team, enemy_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if enemy_team.team_id != team_id:
                distance = self._distance(pos, enemy_pos)
                if distance <= range_distance:
                    if enemy_type == EntityType.BRUTE:
                        total_force += 3
                    elif enemy_type == EntityType.CROSSBOWMAN:
                        total_force += 5
                    elif enemy_type == EntityType.GHAST:
                        total_force += 8

        return total_force

    def _find_nearest_ghast(self, pos, team_id, range_distance=400):
        """Find the nearest enemy GHAST that needs to be focused."""
        closest_ghast = None
        min_distance = float("inf")

        for ent, (ghast_pos, ghast_team, ghast_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ghast_team.team_id != team_id and ghast_type == EntityType.GHAST:
                distance = self._distance(pos, ghast_pos)
                if distance <= range_distance and distance < min_distance:
                    min_distance = distance
                    closest_ghast = (ent, ghast_pos)

        return closest_ghast

    def _handle_ghast_threat(self, ent, pos, attack, team_id, ghast_target, ally_force):
        """Handle GHAST threat with intelligent coordination and base protection."""
        ghast_ent, ghast_pos = ghast_target

        # Check distance from GHAST to our base
        base_pos = self._find_friendly_base(team_id)
        ghast_threatening_base = False
        if base_pos:
            distance_ghast_to_base = self._distance(ghast_pos, base_pos)
            ghast_threatening_base = distance_ghast_to_base <= 300  # GHAST threat range

        # Count available crossbowmen
        ally_crossbowmen = self._count_ally_crossbowmen(ent, team_id)
        brutes_in_combat = self._count_brutes_in_combat(team_id)

        # If GHAST is threatening base, prioritize base defense
        if ghast_threatening_base:
            # Send proportional force to defend base against GHAST
            defenders_needed = min(ally_crossbowmen, 3)  # Max 3 defenders against GHAST
            current_base_defenders = self._count_defenders_near_base(team_id)

            if current_base_defenders < defenders_needed:
                # Not enough defenders - go defend base against GHAST
                self._defend_base_against_ghast(ent, pos, attack, team_id, ghast_target)
                return

        # Check if we have BRUTEs in combat that need support
        if brutes_in_combat > 0 and ally_crossbowmen > 2:
            # Balance between GHAST focus and BRUTE support
            crossbowmen_for_ghast = max(1, int(ally_crossbowmen * 0.5))  # 50% for GHAST

            # Check if we're among the closest to GHAST
            closest_crossbowmen = self._get_closest_crossbowmen_to_target(
                ghast_pos, team_id, crossbowmen_for_ghast
            )
            should_focus_ghast = ent in closest_crossbowmen

            if should_focus_ghast:
                # Focus GHAST with optimal positioning
                self._focus_ghast(ent, pos, ghast_target, attack)
            else:
                # Support BRUTEs while keeping an eye on GHAST
                ally_brute_result = self._find_nearest_ally_brute(ent, pos, team_id)
                if ally_brute_result:
                    brute_ent, brute_pos = ally_brute_result
                    self._coordinate_with_brute(ent, pos, brute_pos, attack, team_id)
        else:
            # Focus entirely on GHAST threat
            self._focus_ghast(ent, pos, ghast_target, attack)

    def _count_defenders_near_base(self, team_id):
        """Count allies currently defending near the base."""
        base_pos = self._find_friendly_base(team_id)
        if not base_pos:
            return 0

        defenders = 0
        for ent, (ally_pos, ally_team, ally_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ally_team.team_id == team_id and ally_type == EntityType.CROSSBOWMAN:
                distance_to_base = self._distance(ally_pos, base_pos)
                if distance_to_base <= 200:  # Within defensive range
                    defenders += 1

        return defenders

    def _defend_base_against_ghast(self, ent, pos, attack, team_id, ghast_target):
        """Specifically defend base against GHAST threat."""
        ghast_ent, ghast_pos = ghast_target
        base_pos = self._find_friendly_base(team_id)

        if not base_pos:
            # Fallback to direct GHAST attack
            self._focus_ghast(ent, pos, ghast_target, attack)
            return

        # Set GHAST as target
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(ghast_ent))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = ghast_ent

        # Position between base and GHAST for intercept
        # Calculate optimal defensive position
        direction_x = ghast_pos.x - base_pos.x
        direction_y = ghast_pos.y - base_pos.y
        length = (direction_x**2 + direction_y**2) ** 0.5

        if length > 0:
            # Position 60% of the way from base to GHAST
            intercept_factor = 0.6
            intercept_x = base_pos.x + (direction_x * intercept_factor)
            intercept_y = base_pos.y + (direction_y * intercept_factor)

            # Clamp to map bounds
            intercept_x = max(32, min(intercept_x, 24 * 32 - 32))
            intercept_y = max(32, min(intercept_y, 24 * 32 - 32))

            intercept_pos = Position(intercept_x, intercept_y)
            distance_to_intercept = self._distance(pos, intercept_pos)

            # Move to intercept position if not already there
            if distance_to_intercept > 40:
                self._smart_move_to(ent, pos, intercept_pos)
            else:
                # Good intercept position - hold and attack
                self._stop_movement(ent)
        else:
            # Fallback - direct attack on GHAST
            self._focus_ghast(ent, pos, ghast_target, attack)

    def _focus_ghast(self, ent, pos, ghast_target, attack):
        """Focus fire on GHAST with optimal positioning."""
        ghast_ent, ghast_pos = ghast_target
        distance = self._distance(pos, ghast_pos)

        # Set GHAST as primary target
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(ghast_ent))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = ghast_ent

        # Maintain optimal range for GHAST combat (slightly closer than normal)
        optimal_range = attack.range * 24 * 0.9  # 90% of max range for better accuracy

        if distance > optimal_range:
            # Get closer to GHAST
            self._smart_move_to(ent, pos, ghast_pos)
        elif distance < optimal_range * 0.6:
            # Too close, back away but keep targeting
            retreat_x = pos.x + (pos.x - ghast_pos.x) * 0.3
            retreat_y = pos.y + (pos.y - ghast_pos.y) * 0.3

            # Clamp to map bounds
            retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
            retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

            destination = Position(retreat_x, retreat_y)
            self._smart_move_to(ent, pos, destination)
        else:
            # Good position - stop and focus fire
            self._stop_movement(ent)

    def _count_brutes_in_combat(self, team_id):
        """Count ally BRUTEs that are currently in combat."""
        brutes_in_combat = 0

        for brute_ent, (brute_pos, brute_team, brute_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if brute_team.team_id == team_id and brute_type == EntityType.BRUTE:
                # Check if BRUTE has enemies nearby (indicating combat)
                enemies_nearby = self._count_nearby_enemies(
                    brute_pos, team_id, range_distance=100
                )
                if enemies_nearby > 0:
                    brutes_in_combat += 1

        return brutes_in_combat

    def _get_closest_crossbowmen_to_target(self, target_pos, team_id, count):
        """Get the N closest crossbowmen to a target position."""
        crossbowmen_distances = []

        for ent, (pos, team, entity_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if team.team_id == team_id and entity_type == EntityType.CROSSBOWMAN:
                distance = self._distance(pos, target_pos)
                crossbowmen_distances.append((ent, distance))

        # Sort by distance and return the closest ones
        crossbowmen_distances.sort(key=lambda x: x[1])
        return [ent for ent, _ in crossbowmen_distances[:count]]

    def _tactical_retreat(self, ent, pos, team_id):
        """Intelligent tactical retreat to defensive position."""
        # Find friendly base (BASTION of same team)
        base_pos = self._find_friendly_base(team_id)
        if base_pos:
            # Retreat towards base but maintain some distance for ranged combat
            retreat_distance = 96  # 3 tiles from base
            direction_x = base_pos.x - pos.x
            direction_y = base_pos.y - pos.y
            length = (direction_x**2 + direction_y**2) ** 0.5

            if length > retreat_distance:
                # Normalize and scale
                direction_x = direction_x / length * retreat_distance
                direction_y = direction_y / length * retreat_distance

                retreat_x = base_pos.x - direction_x
                retreat_y = base_pos.y - direction_y

                # Clamp to map bounds
                retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
                retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

                destination = Position(retreat_x, retreat_y)
                self._smart_move_to(ent, pos, destination)
            else:
                # We're close enough to base - switch to defend mode
                self._defend_base(ent, pos, team_id)
        else:
            # Fallback: retreat to team spawn corner
            if team_id == 2:  # Team 2 spawns bottom-right
                corner_x, corner_y = 20 * 32, 20 * 32
            else:  # Team 1 spawns top-left
                corner_x, corner_y = 4 * 32, 4 * 32
            retreat_pos = Position(corner_x, corner_y)
            self._smart_move_to(ent, pos, retreat_pos)

    def _defend_base(self, ent, pos, team_id):
        """Defend the base by staying near it and attacking approaching enemies."""
        # Find friendly base
        base_pos = self._find_friendly_base(team_id)
        if not base_pos:
            # No base found, fallback to corner defense
            if team_id == 2:
                corner_x, corner_y = 20 * 32, 20 * 32
            else:
                corner_x, corner_y = 4 * 32, 4 * 32
            base_pos = Position(corner_x, corner_y)

        # Look for enemies threatening the base
        enemies_near_base = []
        for ent_enemy, (enemy_pos, enemy_team, enemy_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if enemy_team.team_id != team_id and enemy_type != EntityType.BASTION:
                distance_to_base = self._distance(enemy_pos, base_pos)
                if distance_to_base <= 200:  # Enemies within 200 pixels of base
                    distance_to_self = self._distance(pos, enemy_pos)
                    enemies_near_base.append(
                        (ent_enemy, enemy_pos, enemy_type, distance_to_self)
                    )

        if enemies_near_base:
            # Attack closest enemy threatening the base
            enemies_near_base.sort(key=lambda x: x[3])  # Sort by distance to self
            closest_enemy = enemies_near_base[0]
            enemy_info = (closest_enemy[0], closest_enemy[1], closest_enemy[2])

            # Set target and engage
            if not esper.has_component(ent, Target):
                esper.add_component(ent, Target(closest_enemy[0]))
            else:
                target_comp = esper.component_for_entity(ent, Target)
                target_comp.target_entity_id = closest_enemy[0]

            # Position for optimal defense (maintain distance but stay near base)
            distance_to_enemy = closest_enemy[3]
            optimal_range = 120  # Optimal defensive range

            if distance_to_enemy > optimal_range:
                # Get closer but don't move too far from base
                direction_x = closest_enemy[1].x - pos.x
                direction_y = closest_enemy[1].y - pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    move_distance = min(40, distance_to_enemy - optimal_range)
                    direction_x = direction_x / length * move_distance
                    direction_y = direction_y / length * move_distance

                    new_x = pos.x + direction_x
                    new_y = pos.y + direction_y

                    # Don't move too far from base
                    distance_to_base = self._distance(Position(new_x, new_y), base_pos)
                    if distance_to_base <= 150:  # Stay within 150 pixels of base
                        destination = Position(new_x, new_y)
                        self._smart_move_to(ent, pos, destination)
                    else:
                        self._stop_movement(ent)
            elif distance_to_enemy < optimal_range * 0.7:
                # Too close, back towards base
                direction_x = base_pos.x - pos.x
                direction_y = base_pos.y - pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    direction_x = direction_x / length * 30
                    direction_y = direction_y / length * 30

                    retreat_x = pos.x + direction_x
                    retreat_y = pos.y + direction_y

                    destination = Position(retreat_x, retreat_y)
                    self._smart_move_to(ent, pos, destination)
            else:
                # Good position for defense
                self._stop_movement(ent)
        else:
            # No immediate threats, maintain defensive position near base
            distance_to_base = self._distance(pos, base_pos)
            ideal_defense_distance = 100  # Ideal distance from base for defense

            if distance_to_base > ideal_defense_distance + 30:
                # Too far from base, move closer
                self._smart_move_to(ent, pos, base_pos)
            elif distance_to_base < ideal_defense_distance - 30:
                # Too close to base, move to better defensive position
                direction_x = pos.x - base_pos.x
                direction_y = pos.y - base_pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    direction_x = direction_x / length * ideal_defense_distance
                    direction_y = direction_y / length * ideal_defense_distance

                    defense_x = base_pos.x + direction_x
                    defense_y = base_pos.y + direction_y

                    # Clamp to map bounds
                    defense_x = max(32, min(defense_x, 24 * 32 - 32))
                    defense_y = max(32, min(defense_y, 24 * 32 - 32))

                    destination = Position(defense_x, defense_y)
                    self._smart_move_to(ent, pos, destination)
            else:
                # Good defensive position
                self._stop_movement(ent)

    def _coordinate_with_brute(self, ent, pos, brute_pos, attack, team_id):
        """Advanced coordination with BRUTE ally."""
        # Check if BRUTE is in combat
        brute_enemies = self._count_nearby_enemies(
            brute_pos, team_id, range_distance=120
        )

        if brute_enemies > 0:
            # BRUTE is fighting, provide ranged support - STAY WITH BRUTE
            self._provide_ranged_support(ent, pos, brute_pos, attack, team_id)
        else:
            # BRUTE is moving, follow in formation
            distance_to_brute = self._distance(pos, brute_pos)

            # Don't abandon BRUTE too easily - stay closer
            if distance_to_brute > 150:  # Increased from 80 to 150
                self._follow_brute_for_combat(ent, pos, brute_pos)
            else:
                # Stay in position near BRUTE
                self._stop_movement(ent)

    def _provide_ranged_support(self, ent, pos, brute_pos, attack, team_id):
        """Provide ranged support to fighting BRUTE - PRIORITY: Support the BRUTE!"""
        # Find enemies near the BRUTE
        best_target = None
        min_distance = float("inf")

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if target_team.team_id != team_id and target_type != EntityType.BASTION:
                distance_to_brute = self._distance(brute_pos, target_pos)
                distance_to_self = self._distance(pos, target_pos)

                # Target enemies that are close to BRUTE and in our range
                # Increased range for better BRUTE support
                if (
                    distance_to_brute <= 150
                    and distance_to_self <= attack.range * 24 * 1.2
                ):  # Increased support range
                    if distance_to_self < min_distance:
                        min_distance = distance_to_self
                        best_target = (target_ent, target_pos, target_type)

        if best_target:
            # Attack the enemy threatening our BRUTE
            self._attack_enemy(ent, pos, best_target, attack)
        else:
            # No valid targets in range, get closer to BRUTE to provide better support
            distance_to_brute = self._distance(pos, brute_pos)
            optimal_support_distance = 80  # Stay close to BRUTE for support

            if distance_to_brute > optimal_support_distance + 20:
                # Too far from BRUTE, get closer
                direction_x = brute_pos.x - pos.x
                direction_y = brute_pos.y - pos.y
                length = (direction_x**2 + direction_y**2) ** 0.5

                if length > 0:
                    # Move closer but maintain some distance
                    move_distance = min(
                        40, distance_to_brute - optimal_support_distance
                    )
                    direction_x = direction_x / length * move_distance
                    direction_y = direction_y / length * move_distance

                    new_x = pos.x + direction_x
                    new_y = pos.y + direction_y

                    # Clamp to map bounds
                    new_x = max(32, min(new_x, 24 * 32 - 32))
                    new_y = max(32, min(new_y, 24 * 32 - 32))

                    destination = Position(new_x, new_y)
                    self._smart_move_to(ent, pos, destination)
            else:
                # Good position for support
                self._stop_movement(ent)

    def _aggressive_attack(self, ent, pos, attack, team_id):
        """Aggressive attack behavior when force is superior."""
        # Look for closest enemy to attack
        enemies_in_range = self._find_enemies_in_range(ent, pos, attack, team_id)

        if enemies_in_range:
            # Prioritize targets: GHAST > CROSSBOWMAN > BRUTE
            best_target = self._prioritize_targets(enemies_in_range)
            self._attack_enemy(ent, pos, best_target, attack)
        else:
            # No enemies in range, advance towards enemy base
            self._attack_enemy_base(ent, pos, team_id)

    def _prioritize_targets(self, enemies_in_range):
        """Prioritize targets based on threat level."""
        ghasts = [e for e in enemies_in_range if e[2] == EntityType.GHAST]
        crossbowmen = [e for e in enemies_in_range if e[2] == EntityType.CROSSBOWMAN]
        brutes = [e for e in enemies_in_range if e[2] == EntityType.BRUTE]

        # Priority: GHAST > CROSSBOWMAN > BRUTE
        if ghasts:
            return ghasts[0]
        elif crossbowmen:
            return crossbowmen[0]
        elif brutes:
            return brutes[0]
        else:
            return enemies_in_range[0] if enemies_in_range else None

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
