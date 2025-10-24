"""
AI System for Enemy CROSSBOWMAN Units (Team 2)

This system provides intelligent tactical behavior for CROSSBOWMAN units using
a modular architecture with specialized helper classes for complex behaviors.

Core Features:
- Terrain-aware pathfinding integration with A* algorithm
- Advanced BRUTE coordination with never-abandon policy
- Proportional base defense with threat assessment
- Intelligent target prioritization and force evaluation
- Streamlined decision making with clear behavioral hierarchies

Architecture:
- Main AI system handles core decision flow and coordination
- Helper classes manage specialized behaviors (BruteCoordination, BaseDefense, etc.)
- Modular design allows easy maintenance and behavior modification
- Consistent English documentation and clear code structure

Tactical Priorities:
1. BRUTE coordination (never abandon allied BRUTE in combat)
2. Force evaluation and tactical decision making
3. Base defense with proportional reinforcements
4. Target prioritization and optimal positioning
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
from systems.ai_helpers import (
    BruteCoordination,
    BaseDefenseManager,
    TargetPrioritizer,
    MovementController,
)


class CrossbowmanAISystemEnemy(esper.Processor):
    """
    AI system for CROSSBOWMAN units of team 2 with modular tactical behavior.

    This system provides comprehensive tactical intelligence using specialized
    helper classes to manage complex behaviors while maintaining clean,
    maintainable code structure.

    Key Behavioral Features:
    - Never abandon BRUTE allies during combat (absolute priority)
    - Proportional base defense with threat assessment
    - Intelligent force evaluation and tactical adaptation
    - Advanced target prioritization and positioning
    """

    def __init__(self, pathfinding_system):
        """
        Initialize the AI system with helper class instances.

        Args:
            pathfinding_system: Reference to pathfinding system for terrain data
        """
        super().__init__()
        self.pathfinding_system = pathfinding_system
        self.terrain_map = getattr(pathfinding_system, "terrain_map", {})

        # Initialize specialized helper classes for modular behavior
        self.brute_coordinator = BruteCoordination(self)
        self.base_defense = BaseDefenseManager(self)
        self.target_prioritizer = TargetPrioritizer(self)
        self.movement_controller = MovementController(self)

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
        """
        Main AI decision-making with streamlined tactical logic.

        Decision Flow:
        1. Continue pathfinding if active
        2. Handle immediate enemies in range
        3. Make strategic tactical decision based on battlefield state

        Args:
            ent: Entity ID
            pos (Position): Current unit position
            attack (Attack): Unit's attack component
            team_id (int): Team ID for ally/enemy identification
        """
        # Priority 1: Continue active pathfinding
        if self._is_following_path(ent):
            return

        # Priority 2: Handle immediate combat targets
        enemies_in_range = self._find_enemies_in_range(ent, pos, attack, team_id)
        if enemies_in_range and not self._has_brute_allies(team_id):
            # No BRUTE coordination needed - engage directly
            best_target = self.target_prioritizer.prioritize_targets(enemies_in_range)
            self._attack_enemy(ent, pos, best_target, attack)
            return

        # Priority 3: Strategic tactical decision making
        self._make_tactical_decision(ent, pos, attack, team_id)

    def _make_tactical_decision(self, ent, pos, attack, team_id):
        """
        Streamlined tactical decision making using modular helper classes.

        Priority System:
        1. BRUTE coordination (never abandon BRUTE allies in combat)
        2. GHAST threat handling (high-value target elimination)
        3. Base defense (proportional reinforcement system)
        4. Force evaluation and strategy selection
        """
        # ABSOLUTE PRIORITY: Never abandon BRUTE allies in combat
        nearby_brute_in_combat = self.brute_coordinator.find_brute_in_combat_nearby(
            ent, pos, team_id
        )
        if nearby_brute_in_combat:
            self._stay_and_fight_with_brute(
                ent, pos, attack, team_id, nearby_brute_in_combat
            )
            return

        # HIGH PRIORITY: GHAST threat elimination
        ghast_target = self.target_prioritizer.find_nearest_ghast(
            pos, team_id, range_distance=400
        )
        if ghast_target:
            self._handle_ghast_threat(ent, pos, attack, team_id, ghast_target)
            return

        # BRUTE COORDINATION: Intelligent support distribution
        ally_brutes = self.brute_coordinator.get_all_ally_brutes(team_id)
        if ally_brutes:
            self._coordinate_brute_support(ent, pos, attack, team_id, ally_brutes)
            return

        # BASE DEFENSE: Proportional reinforcement system
        if self.base_defense.is_base_under_attack(team_id):
            attackers_count = self.base_defense.count_enemies_attacking_base(team_id)
            defenders_needed = self.base_defense.calculate_defenders_needed(
                attackers_count
            )
            current_defenders = self.base_defense.count_current_defenders(team_id)

            if current_defenders < defenders_needed:
                self._defend_base_actively(ent, pos, team_id)
                return

        # FORCE EVALUATION: Strategic behavior selection
        self._execute_force_based_strategy(ent, pos, attack, team_id)

    def _is_following_path(self, ent):
        """Check if unit is currently following an A* pathfinding route."""
        if esper.has_component(ent, PathRequest):
            path_request = esper.component_for_entity(ent, PathRequest)
            return self._follow_astar_path(
                ent, esper.component_for_entity(ent, Position), path_request
            )
        return False

    def _has_brute_allies(self, team_id):
        """Quick check if team has any BRUTE allies available."""
        return self._count_ally_brutes(team_id) > 0

    def _execute_force_based_strategy(self, ent, pos, attack, team_id):
        """Execute strategy based on force evaluation and tactical situation."""
        # Calculate force balance
        ally_force = self._calculate_ally_force(ent, team_id, pos)
        enemy_force = self._calculate_enemy_force(team_id, pos, range_distance=300)
        force_ratio = ally_force / max(enemy_force, 1)  # Avoid division by zero

        # Strategy selection based on force ratio
        if force_ratio < 0.5:  # Outnumbered
            self._tactical_retreat(ent, pos, team_id)
        elif force_ratio >= 0.8 and force_ratio <= 1.2:  # Equal forces
            self._attack_enemies_then_base(ent, pos, attack, team_id)
        else:  # Superior force
            self._coordinated_group_attack(ent, pos, attack, team_id)

    def _stay_and_fight_with_brute(self, ent, pos, attack, team_id, brute_info):
        """
        NEVER ABANDON BRUTE IN COMBAT - Stay and fight with unwavering loyalty.

        This method implements the core principle that CROSSBOWMAN units must
        never flee when supporting a BRUTE ally engaged in combat.
        """
        brute_pos = brute_info["position"]
        brute_ent = brute_info["entity"]

        # Find and prioritize threats to the BRUTE
        priority_targets = self._find_brute_threats(
            ent, pos, attack, team_id, brute_pos
        )

        if priority_targets:
            # Attack the highest priority threat to our BRUTE
            best_target = max(priority_targets, key=lambda x: x[3])
            target_info = (best_target[0], best_target[1], best_target[2])

            # Set combat target
            self._set_combat_target(ent, best_target[0])

            # Position optimally for BRUTE support
            self.movement_controller.position_for_brute_support(
                ent, pos, brute_pos, target_info[1], attack
            )
        else:
            # No immediate threats - maintain support formation
            self._maintain_brute_support_position(ent, pos, brute_pos)

    def _find_brute_threats(self, ent, pos, attack, team_id, brute_pos):
        """Find and prioritize enemies threatening our BRUTE ally."""
        priority_targets = []

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if (
                target_team.team_id != team_id
                and target_type != EntityType.BASTION
                and self._is_alive(target_ent)
            ):

                distance_to_brute = self._distance(brute_pos, target_pos)
                distance_to_self = self._distance(pos, target_pos)

                # Check if enemy is threatening BRUTE and within our support range
                if (
                    distance_to_brute <= 150
                    and distance_to_self <= attack.range * 24 * 1.5
                ):

                    priority = self.target_prioritizer.calculate_brute_support_priority(
                        target_type, distance_to_brute, distance_to_self
                    )
                    priority_targets.append(
                        (target_ent, target_pos, target_type, priority)
                    )

        return priority_targets

    def _set_combat_target(self, ent, target_ent):
        """Set or update the combat target for this unit."""
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(target_ent))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = target_ent

    def _maintain_brute_support_position(self, ent, pos, brute_pos):
        """Maintain optimal support position near BRUTE when no threats present."""
        distance_to_brute = self._distance(pos, brute_pos)
        ideal_support_distance = 90

        if distance_to_brute > ideal_support_distance + 30:
            # Too far - get closer to BRUTE
            self._smart_move_to(ent, pos, brute_pos)
        elif distance_to_brute < ideal_support_distance - 20:
            # Too close - maintain optimal distance
            self._move_to_support_distance(ent, pos, brute_pos, ideal_support_distance)
        else:
            # Perfect support position
            self._stop_movement(ent)

    def _move_to_support_distance(self, ent, pos, brute_pos, target_distance):
        """Move to maintain specific distance from BRUTE ally."""
        direction_x = pos.x - brute_pos.x
        direction_y = pos.y - brute_pos.y
        length = (direction_x**2 + direction_y**2) ** 0.5

        if length > 0:
            direction_x = direction_x / length * target_distance
            direction_y = direction_y / length * target_distance

            new_x = brute_pos.x + direction_x
            new_y = brute_pos.y + direction_y

            # Clamp to map bounds
            new_x = max(32, min(new_x, 24 * 32 - 32))
            new_y = max(32, min(new_y, 24 * 32 - 32))

            destination = Position(new_x, new_y)
            self._smart_move_to(ent, pos, destination)

    def _handle_ghast_threat(self, ent, pos, attack, team_id, ghast_target):
        """
        Handle GHAST threat with intelligent coordination and positioning.

        GHASTs are high-value targets that require immediate attention due to
        their devastating ranged attacks and threat to both units and base.
        """
        ghast_ent, ghast_pos = ghast_target

        # Check if GHAST is threatening our base
        base_pos = self._find_friendly_base(team_id)
        ghast_threatening_base = False
        if base_pos:
            distance_ghast_to_base = self._distance(ghast_pos, base_pos)
            ghast_threatening_base = distance_ghast_to_base <= 300

        if ghast_threatening_base:
            # GHAST threatens base - intercept and defend
            self._defend_base_against_ghast(ent, pos, attack, team_id, ghast_target)
        else:
            # Standard GHAST engagement with optimal positioning
            self._focus_ghast(ent, pos, ghast_target, attack)

    def _defend_base_actively(self, ent, pos, team_id):
        """
        Execute active base defense with aggressive threat engagement.

        Uses the BaseDefenseManager to identify threats and position optimally
        for defensive combat while maintaining base proximity.
        """
        base_pos = self._find_friendly_base(
            team_id
        ) or self._get_fallback_base_position(team_id)

        # Find and engage the most threatening enemy
        closest_threat = self.base_defense.find_base_threat(pos, team_id)

        if closest_threat:
            # Engage threat while maintaining defensive positioning
            enemy_ent, enemy_pos, enemy_type = closest_threat
            self._set_combat_target(ent, enemy_ent)
            self._position_for_base_defense(ent, pos, enemy_pos, base_pos)
        else:
            # No immediate threats - maintain defensive perimeter
            self.movement_controller.position_defensively_near_base(ent, pos, team_id)

    def _position_for_base_defense(self, ent, pos, enemy_pos, base_pos):
        """Position optimally for base defense engagement."""
        distance_to_enemy = self._distance(pos, enemy_pos)
        distance_to_base = self._distance(pos, base_pos)
        optimal_range = 100  # Aggressive defensive range

        if distance_to_enemy > optimal_range and distance_to_base <= 200:
            # Close with enemy if not too far from base
            self._move_closer_to_target(ent, pos, enemy_pos, optimal_range)
        elif distance_to_enemy < optimal_range * 0.6:
            # Too close - retreat toward base
            self._retreat_toward_base(ent, pos, enemy_pos, base_pos)
        else:
            # Good defensive position
            self._stop_movement(ent)

    def _get_fallback_base_position(self, team_id):
        """Get fallback position when no base found."""
        if team_id == 2:
            return Position(20 * 32, 20 * 32)
        else:
            return Position(4 * 32, 4 * 32)

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
        """Balanced strategy: attack nearby enemies first, then enemy base."""
        # Priority 1: Engage enemies in range
        enemies_in_range = self._find_enemies_in_range(ent, pos, attack, team_id)
        if enemies_in_range:
            best_target = self.target_prioritizer.prioritize_targets(enemies_in_range)
            self._attack_enemy(ent, pos, best_target, attack)
            return

        # Priority 2: Seek enemies on map
        closest_enemy = self.target_prioritizer.find_closest_enemy_on_map(
            ent, pos, team_id
        )
        if closest_enemy:
            self._engage_or_approach_enemy(ent, pos, attack, closest_enemy)
        else:
            # Priority 3: Attack enemy base
            self._attack_enemy_base(ent, pos, team_id)

    def _engage_or_approach_enemy(self, ent, pos, attack, enemy_info):
        """Engage enemy if in range, otherwise approach for engagement."""
        enemy_ent, enemy_pos, enemy_type = enemy_info
        distance_to_enemy = self._distance(pos, enemy_pos)

        if distance_to_enemy <= attack.range * 24 * 1.2:  # Extended engagement range
            self._attack_enemy(ent, pos, enemy_info, attack)
        else:
            self._smart_move_to(ent, pos, enemy_pos)

    def _find_enemies_in_range(self, ent, pos, attack, team_id):
        """
        Find all living enemies within attack range for targeting.

        Returns list of (entity_id, position, entity_type) tuples for
        hostile units that can be engaged immediately.
        """
        enemies = []
        attack_range = attack.range * 24  # Convert tiles to pixels

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            # Filter: exclude self, allies, bastions, and dead units
            if (
                target_ent == ent
                or target_team.team_id == team_id
                or target_team.team_id != 1  # Only target enemy team 1
                or target_type == EntityType.BASTION
                or not self._is_alive(target_ent)
            ):
                continue

            # Check if target is within attack range
            if self._distance(pos, target_pos) <= attack_range:
                enemies.append((target_ent, target_pos, target_type))

        return enemies

    def _is_alive(self, ent):
        """Check if entity is alive (has health > 0)."""
        if esper.has_component(ent, Health):
            health = esper.component_for_entity(ent, Health)
            return health.remaining > 0
        return True  # Assume alive if no health component

    def _move_closer_to_target(self, ent, pos, target_pos, optimal_range):
        """Move unit closer to target while maintaining optimal combat range."""
        distance_to_target = self._distance(pos, target_pos)
        if distance_to_target > optimal_range:
            move_distance = min(40, distance_to_target - optimal_range)
            direction_x = target_pos.x - pos.x
            direction_y = target_pos.y - pos.y
            length = (direction_x**2 + direction_y**2) ** 0.5

            if length > 0:
                direction_x = direction_x / length * move_distance
                direction_y = direction_y / length * move_distance

                new_x = pos.x + direction_x
                new_y = pos.y + direction_y

                # Clamp to map bounds
                new_x = max(32, min(new_x, 24 * 32 - 32))
                new_y = max(32, min(new_y, 24 * 32 - 32))

                destination = Position(new_x, new_y)
                self._smart_move_to(ent, pos, destination)

    def _retreat_toward_base(self, ent, pos, enemy_pos, base_pos):
        """Retreat toward base while maintaining engagement distance."""
        retreat_x = pos.x + (base_pos.x - enemy_pos.x) * 0.3
        retreat_y = pos.y + (base_pos.y - enemy_pos.y) * 0.3

        # Clamp to map bounds
        retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
        retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

        destination = Position(retreat_x, retreat_y)
        self._smart_move_to(ent, pos, destination)

    def _attack_enemy(self, ent, pos, enemy_info, attack):
        """
        Attack enemy with optimal crossbow combat positioning.

        Maintains 80% of maximum range for optimal effectiveness while
        avoiding melee combat and terrain obstacles.
        """
        enemy_id, enemy_pos, enemy_type = enemy_info
        distance = self._distance(pos, enemy_pos)

        # Set combat target
        self._set_combat_target(ent, enemy_id)

        # Execute optimal combat positioning
        optimal_range = attack.range * 24 * 0.8  # 80% of max range

        if distance < optimal_range * 0.7:
            # Too close - retreat to optimal range
            self._retreat_from_enemy_combat(ent, pos, enemy_pos)
        elif distance > optimal_range:
            # Too far - advance to optimal range
            self._smart_move_to(ent, pos, enemy_pos)
        else:
            # Perfect range - hold position and fire
            self._stop_movement(ent)

    def _retreat_from_enemy_combat(self, ent, pos, enemy_pos):
        """Retreat from enemy to maintain optimal combat distance."""
        retreat_x = pos.x + (pos.x - enemy_pos.x) * 0.5
        retreat_y = pos.y + (pos.y - enemy_pos.y) * 0.5

        # Clamp to map bounds
        retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
        retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

        destination = Position(retreat_x, retreat_y)
        self._smart_move_to(ent, pos, destination)

    def _count_ally_brutes(self, team_id):
        """Count allied BRUTE units for tactical decision making."""
        count = 0
        for ent, (team, entity_type) in esper.get_components(Team, EntityType):
            if team.team_id == team_id and entity_type == EntityType.BRUTE:
                count += 1
        return count

    def _coordinate_brute_support(self, ent, pos, attack, team_id, ally_brutes):
        """
        Intelligent BRUTE support coordination using helper class analysis.

        Assigns this crossbowman to the BRUTE that needs support most urgently
        based on combat status, current support levels, and tactical priorities.
        """
        # Get all crossbowmen for distribution analysis
        all_crossbowmen = self._get_all_allied_crossbowmen(team_id)

        # Calculate current support levels
        for brute in ally_brutes:
            brute["supporting_crossbowmen"] = self._count_crossbowmen_supporting_brute(
                brute["position"], all_crossbowmen
            )

        # Find BRUTE needing support most
        best_brute = self.brute_coordinator.find_brute_needing_support(
            ally_brutes, all_crossbowmen
        )

        if best_brute:
            self._provide_dedicated_brute_support(ent, pos, attack, team_id, best_brute)
        else:
            # Fallback: support nearest BRUTE
            nearest_brute = min(
                ally_brutes, key=lambda b: self._distance(pos, b["position"])
            )
            self._provide_dedicated_brute_support(
                ent, pos, attack, team_id, nearest_brute
            )

    def _get_all_allied_crossbowmen(self, team_id):
        """Get list of all allied CROSSBOWMAN units with positions."""
        crossbowmen = []
        for crossbow_ent, (team, entity_type, crossbow_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if team.team_id == team_id and entity_type == EntityType.CROSSBOWMAN:
                crossbowmen.append({"entity": crossbow_ent, "position": crossbow_pos})
        return crossbowmen

    def _count_crossbowmen_supporting_brute(self, brute_pos, all_crossbowmen):
        """Count crossbowmen currently supporting a specific BRUTE."""
        support_count = 0
        for crossbow in all_crossbowmen:
            distance = self._distance(crossbow["position"], brute_pos)
            if distance <= 150:  # Support range
                support_count += 1
        return support_count

    def _provide_dedicated_brute_support(self, ent, pos, attack, team_id, brute_info):
        """
        Provide unwavering support to assigned BRUTE ally.

        Never abandons BRUTE in combat - maintains formation when moving
        and fights alongside BRUTE during engagements.
        """
        brute_pos = brute_info["position"]
        in_combat = brute_info["in_combat"]

        if in_combat:
            # BRUTE fighting - NEVER ABANDON: Stay and fight together
            self._stay_and_fight_with_brute(ent, pos, attack, team_id, brute_info)
        else:
            # BRUTE moving - maintain formation for immediate support
            self._maintain_formation_with_brute(ent, pos, brute_pos)

    def _maintain_formation_with_brute(self, ent, pos, brute_pos):
        """Maintain tactical formation with BRUTE ally during movement."""
        distance_to_brute = self._distance(pos, brute_pos)
        optimal_follow_distance = 80

        if distance_to_brute > optimal_follow_distance + 30:
            # Too far - close formation
            self._smart_move_to(ent, pos, brute_pos)
        elif distance_to_brute < optimal_follow_distance - 20:
            # Too close - maintain optimal support distance
            self._move_to_support_distance(ent, pos, brute_pos, optimal_follow_distance)
        else:
            # Perfect formation - ready for combat
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
