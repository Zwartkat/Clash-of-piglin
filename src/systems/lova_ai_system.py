"""crossbowman_ai_system_enemy

Enemy CROSSBOWMAN AI processor used for team 2. Provides tactical
decision-making for ranged infantry: target selection, group tactics,
base defense and BRUTE support. The system relies on helper classes
for specialized behaviors (brute coordination, base defense, movement
and target prioritization).

This module only contains documentation and helpers for maintainers.
Runtime behavior is implemented in the methods of
``CrossbowmanAISystemEnemy``.

Important concepts:
- Force evaluation: point-based estimate of allied vs enemy power.
- Group assault: recruit nearby allies to focus fire on a chosen enemy.
- BRUTE support: never abandon BRUTEs engaged in combat.
"""

import math
import esper
from components.ai import AIMemory, AIState, AIStateType, PathRequest
from components.gameplay.attack import Attack
from components.base.health import Health
from core.accessors import get_ai_mapping
from core.game.map import Map
from components.base.position import Position
from components.gameplay.target import Target
from components.base.team import Team
from components.base.velocity import Velocity
from enums.case_type import CaseType
from enums.entity.entity_type import EntityType
from core.ecs.event_bus import EventBus
from enums.entity.unit_type import UnitType
from events.event_move import EventMoveTo
from systems.ai_helpers import (
    BruteCoordination,
    BaseDefenseManager,
    TargetPrioritizer,
    MovementController,
)


class LOVAAiSystem(esper.Processor):
    """Processor that implements tactical behaviour for enemy crossbowmen.

    The processor is responsible for evaluating the local battlefield and
    issuing movement and targeting orders through the game's event system.

    Attributes:
        pathfinding_system: reference to the pathfinder for A* requests.
        brute_coordinator: helper managing BRUTE support assignments.
        base_defense: helper that finds and ranks threats to the bastion.
        target_prioritizer: helper to rank potential targets.
        movement_controller: helper for movement/positioning behaviors.
    """

    def __init__(self, pathfinding_system):
        """Create a new CrossbowmanAISystemEnemy.

        Args:
            pathfinding_system: object providing terrain and pathfinding APIs.
        """
        super().__init__()
        self.pathfinding_system = pathfinding_system
        self.terrain_map = getattr(pathfinding_system, "terrain_map", {})

        # Initialize specialized helper classes for modular behavior
        self.brute_coordinator = BruteCoordination(self)
        self.base_defense = BaseDefenseManager(self)
        self.target_prioritizer = TargetPrioritizer(self)
        self.movement_controller = MovementController(self)

        self.ai_mapping = get_ai_mapping()

    def process(self, dt):
        """Run AI update for all enemy crossbowmen.

        This method prepares per-tick structures (assignment counters) and
        iterates over all relevant entities to run ``_smart_ai_behavior``.

        Args:
            dt (float): delta time since last frame (unused by this processor
                but required by the esper API).
        """
        # Temporary map to track brute assignment counts during this AI tick.
        # This helps distribute crossbowmen across multiple brutes instead of
        # all selecting the same target.
        self._brute_assignment_counts = {}

        # Add AI components to team 2 CROSSBOWMAN units
        for ent, (team, entity_type, pos, attack, health) in esper.get_components(
            Team, EntityType, Position, Attack, Health
        ):

            if self._is_lova_ai(entity_type, team.team_id):  # Enemy team
                # Add AI components if missing
                if not esper.has_component(ent, AIState):
                    esper.add_component(ent, AIState())
                if not esper.has_component(ent, AIMemory):
                    esper.add_component(ent, AIMemory())
                if not esper.has_component(ent, PathRequest):
                    esper.add_component(ent, PathRequest())

        # Pre-fill assignment counts from existing AIMemory to preserve
        # previous frame assignments and avoid flapping.
        for mem_ent, (memory,) in esper.get_components(AIMemory):
            try:
                assigned = memory.assigned_brute_id
                if assigned:
                    self._brute_assignment_counts[assigned] = (
                        self._brute_assignment_counts.get(assigned, 0) + 1
                    )
            except Exception:
                pass

        # Process all units with AI
        for ent, (
            team,
            entity_type,
            pos,
            attack,
            health,
            ai_state,
        ) in esper.get_components(Team, EntityType, Position, Attack, Health, AIState):
            if not self._is_lova_ai(entity_type, team.team_id):
                continue

            # Smart AI logic with pathfinding
            self._smart_ai_behavior(ent, pos, attack, team.team_id)

    def _is_lova_ai(self, entity_type: EntityType, team_id: int) -> bool:
        """
        Check if entity have a LOVA AI
        Args:
            entity_type (_type_): Entity type of entity
            team_id (_type_): Team id of entity

        Returns:
            bool : True if there is a LOVA Ai else False
        """

        availables_ai = self.ai_mapping[entity_type]
        if not availables_ai:
            return False

        ai = availables_ai[team_id]

        if not ai == "LOVA":
            return False
        return True

    def _smart_ai_behavior(self, ent, pos, attack, team_id):
        """Top-level decision flow for a single crossbowman.

        The method evaluates immediate, high-priority concerns first (active
        path following and base-under-attack), then looks for GHASTs (highest
        priority) and immediate enemies. If no immediate action is required it
        delegates to ``_make_tactical_decision`` for strategic behavior.

        Args:
            ent (int): entity id
            pos (Position): current position component
            attack (Attack): unit attack stats component
            team_id (int): integer team id for friend/foe checks

        Returns:
            None
        """
        # Priority 1: Continue active pathfinding
        if self._is_following_path(ent):
            return

        # Emergency priority: if our base is under attack, abandon everything
        # and defend it immediately. This must preempt GHAST and other tasks
        # so defenders don't stay in a corner when the bastion is threatened.
        try:
            if self.base_defense.is_base_under_attack(team_id):
                self._defend_base_actively(ent, pos, team_id)
                return
        except Exception:
            # Defensive check failed for some reason; continue normal flow
            pass

        # Priority 2: Check for GHAST first - ALWAYS prioritize GHAST over everything else
        ghast_target = self.target_prioritizer.find_nearest_ghast(
            pos, team_id, range_distance=600
        )
        if ghast_target:
            # GHAST detected - abandon everything else and focus fire
            self._handle_ghast_threat(ent, pos, attack, team_id, ghast_target)
            return

        # Priority 3: Handle immediate combat targets
        enemies_in_range = self._find_enemies_in_range(ent, pos, attack, team_id)
        if enemies_in_range and not self._has_brute_allies(team_id):
            # No BRUTE coordination needed - engage directly
            best_target = self.target_prioritizer.prioritize_targets(enemies_in_range)
            self._attack_enemy(ent, pos, best_target, attack)
            return

        # Priority 3: Strategic tactical decision making
        self._make_tactical_decision(ent, pos, attack, team_id)

    def _make_tactical_decision(self, ent, pos, attack, team_id):
        """Choose a mid-to-long-term tactical action for the unit.

        The decision order encodes tactical priorities: GHAST elimination,
        BRUTE support, coordinated BRUTE assistance, base defense and finally
        force-based strategies (assault, retreat or probing objectives).

        Args:
            ent (int): entity id
            pos (Position): unit position
            attack (Attack): unit attack component
            team_id (int): team identifier

        Returns:
            None
        """
        # ULTIMATE PRIORITY: GHAST threat elimination - ALWAYS comes first, even before BRUTE support
        ghast_target = self.target_prioritizer.find_nearest_ghast(
            pos,
            team_id,
            range_distance=600,  # INCREASED from 400 to 600 - larger detection range
        )
        if ghast_target:
            self._handle_ghast_threat(ent, pos, attack, team_id, ghast_target)
            return

        # ABSOLUTE PRIORITY: Never abandon BRUTE allies in combat (but only if no GHAST)
        nearby_brute_in_combat = self.brute_coordinator.find_brute_in_combat_nearby(
            ent, pos, team_id
        )
        if nearby_brute_in_combat:
            self._stay_and_fight_with_brute(
                ent, pos, attack, team_id, nearby_brute_in_combat
            )
            return

        # BRUTE COORDINATION: Intelligent support distribution
        ally_brutes = self.brute_coordinator.get_all_ally_brutes(team_id)
        if ally_brutes:
            self._coordinate_brute_support(ent, pos, attack, team_id, ally_brutes)
            return

        # BASE DEFENSE: If the base is under attack, actively defend it now.
        # Previously we only sent reinforcements when defenders were lacking.
        # Change: every crossbowman will execute active base defense behavior so
        # they patrol the bastion and engage attackers immediately.
        if self.base_defense.is_base_under_attack(team_id):
            self._defend_base_actively(ent, pos, team_id)
            return

        # FORCE EVALUATION: Strategic behavior selection
        self._execute_force_based_strategy(ent, pos, attack, team_id)

    def _is_following_path(self, ent):
        """Return True if the entity currently has an active A* PathRequest.

        Args:
            ent (int): entity id

        Returns:
            bool: True when a valid path is being followed, False otherwise.
        """
        if esper.has_component(ent, PathRequest):
            path_request = esper.component_for_entity(ent, PathRequest)
            return self._follow_astar_path(
                ent, esper.component_for_entity(ent, Position), path_request
            )
        return False

    def _has_brute_allies(self, team_id):
        """Return True when the team has any BRUTE units alive.

        Args:
            team_id (int): team to check

        Returns:
            bool
        """
        return self._count_ally_brutes(team_id) > 0

    def _execute_force_based_strategy(self, ent, pos, attack, team_id):
        """Evaluate nearby force and select an appropriate strategy.

        Uses a simple point-based force estimator and local unit counts to
        decide between group assaults, coordinated attacks, probing towards
        the enemy base or tactical retreats.

        Args:
            ent (int): entity id
            pos (Position): unit position
            attack (Attack): unit attack component
            team_id (int): team identifier

        Returns:
            None
        """
        # Calculate force balance
        ally_force = self._calculate_ally_force(ent, team_id, pos)
        enemy_force = self._calculate_enemy_force(team_id, pos, range_distance=300)
        force_ratio = ally_force / max(enemy_force, 1)  # Avoid division by zero
        # Quick numeric check (allies vs enemies nearby) to prefer group assault
        nearby_ally_count = self._count_ally_crossbowmen(ent, team_id)
        nearby_enemy_count = self._count_nearby_enemies(
            pos, team_id, range_distance=400
        )

        # If there are enemies and our allied force (point-based) is >= enemy force,
        # prefer to attack (group assault if enemies are nearby, otherwise seek enemies/base).
        # This ensures units don't unnecessarily retreat when they are at least equal in strength.
        if enemy_force > 0 and ally_force >= enemy_force:
            if nearby_enemy_count > 0:
                self._group_assault(ent, pos, attack, team_id)
            else:
                self._attack_enemies_then_base(ent, pos, attack, team_id)
            return

        # If there are no enemies nearby, seek the enemy base
        if enemy_force == 0 and nearby_enemy_count == 0:
            self._attack_enemies_then_base(ent, pos, attack, team_id)
            return

        # If allied units outnumber local enemies, do a coordinated group assault
        if nearby_enemy_count > 0 and nearby_ally_count >= nearby_enemy_count:
            self._group_assault(ent, pos, attack, team_id)
            return

        # If allied force (point-based) is superior, perform a coordinated group assault
        if ally_force > enemy_force:
            self._group_assault(ent, pos, attack, team_id)
            return

        # Strategy selection based on force ratio for the remaining cases
        if force_ratio < 0.5:  # Outnumbered
            self._tactical_retreat(ent, pos, team_id)
        elif 0.8 <= force_ratio <= 1.2:  # Equal forces
            self._attack_enemies_then_base(ent, pos, attack, team_id)
        else:  # Slight superiority
            self._coordinated_group_attack(ent, pos, attack, team_id)
            return

    def _group_assault(self, ent, pos, attack, team_id):
        """Form a temporary fire team and order participating allies to engage.

        The method recruits nearby crossbowmen, selects a focal enemy using
        the prioritizer and commands participants to form a loose circle at a
        safe firing distance. If no local enemies are found it will order a
        grouped approach to the enemy base instead.

        Args:
            ent (int): invoking entity id
            pos (Position): position of invoking unit
            attack (Attack): attack component of invoking unit
            team_id (int): team identifier

        Returns:
            None
        """
        RECRUIT_RADIUS = 500

        # Gather nearby enemy units
        nearby_enemies = []
        for enemy_ent, (e_pos, e_team, e_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if (
                e_team.team_id != team_id
                and e_type != EntityType.BASTION
                and self._is_alive(enemy_ent)
            ):
                if self._distance(pos, e_pos) <= RECRUIT_RADIUS:
                    nearby_enemies.append((enemy_ent, e_pos, e_type))

        # If no nearby enemies, fall back to attacking enemy base as group
        if not nearby_enemies:
            enemy_team_id = 1 if team_id == 2 else 2
            enemy_base_pos = self._find_enemy_base(enemy_team_id)
            if enemy_base_pos:
                allies = self._get_closest_crossbowmen_to_target(
                    enemy_base_pos, team_id, self._count_ally_crossbowmen(ent, team_id)
                )
                for idx, ally_ent in enumerate(allies):
                    try:
                        ally_pos = esper.component_for_entity(ally_ent, Position)
                    except Exception:
                        continue
                    angle = (idx / max(1, len(allies))) * 2 * math.pi
                    spread = 60 + (idx % 4) * 12
                    dest_x = enemy_base_pos.x + math.cos(angle) * spread
                    dest_y = enemy_base_pos.y + math.sin(angle) * spread
                    destination = Position(
                        max(32, min(dest_x, 24 * 32 - 32)),
                        max(32, min(dest_y, 24 * 32 - 32)),
                    )
                    self._smart_move_to(ally_ent, ally_pos, destination)
                return

        # Choose focal enemy using existing prioritizer if possible
        focal = None
        if nearby_enemies:
            try:
                focal = self.target_prioritizer.prioritize_targets(nearby_enemies)
            except Exception:
                focal = nearby_enemies[0]

        if not focal:
            return

        enemy_ent, enemy_pos, enemy_type = focal

        # Determine allies able to participate (within a larger radius)
        allies_info = self._get_all_allied_crossbowmen(team_id)
        participating = [
            c["entity"]
            for c in allies_info
            if self._distance(c["position"], enemy_pos) <= RECRUIT_RADIUS
        ]

        if not participating:
            # No close allies, include some closest ones
            participating = self._get_closest_crossbowmen_to_target(
                enemy_pos, team_id, min(6, self._count_ally_crossbowmen(ent, team_id))
            )

        # Determine standoff distance based on attacker's range
        safe_distance = (
            attack.range * 24 * 0.85 if attack and hasattr(attack, "range") else 100
        )

        # Issue orders: spread around the enemy at safe_distance
        for idx, ally_ent in enumerate(participating):
            try:
                ally_pos = esper.component_for_entity(ally_ent, Position)
            except Exception:
                continue

            angle = (idx / max(1, len(participating))) * 2 * math.pi
            spread = 20 + (idx % 3) * 8
            dest_x = enemy_pos.x + math.cos(angle) * (safe_distance + spread)
            dest_y = enemy_pos.y + math.sin(angle) * (safe_distance + spread)
            destination = Position(
                max(32, min(dest_x, 24 * 32 - 32)),
                max(32, min(dest_y, 24 * 32 - 32)),
            )

            # Assign target and move
            if not esper.has_component(ally_ent, Target):
                esper.add_component(ally_ent, Target(enemy_ent))
            else:
                tcomp = esper.component_for_entity(ally_ent, Target)
                tcomp.target_entity_id = enemy_ent

            self._smart_move_to(ally_ent, ally_pos, destination)

        # Ensure current unit is also ordered
        self._set_combat_target(ent, enemy_ent)
        self._smart_move_to(ent, pos, enemy_pos)

    def _stay_and_fight_with_brute(self, ent, pos, attack, team_id, brute_info):
        """Provide immediate support to a BRUTE that is currently in combat.

        The method finds high-priority threats to the BRUTE and either attacks
        them or maintains an optimal support position when no threats are
        currently present.

        Args:
            ent (int): entity id of the crossbowman
            pos (Position): crossbowman position
            attack (Attack): attack component
            team_id (int): team identifier
            brute_info (dict): information about the BRUTE (position, entity id,
                combat status, ...)

        Returns:
            None
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
        """Scan for enemies that pose a threat to a BRUTE ally and rank them.

        Args:
            ent (int): entity id of the crossbowman
            pos (Position): crossbowman position
            attack (Attack): attack component
            team_id (int): team identifier
            brute_pos (Position): BRUTE position to evaluate threats around

        Returns:
            list: tuples of (entity, position, entity_type, priority)
        """
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
        """Attach or update the ``Target`` component with ``target_ent``.

        Args:
            ent (int): entity id
            target_ent (int): target entity id

        Returns:
            None
        """
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(target_ent))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = target_ent

    def _maintain_brute_support_position(self, ent, pos, brute_pos):
        """Keep formation near a BRUTE when there are no immediate threats.

        The method adjusts position to remain inside a tight support bubble.

        Args:
            ent (int): entity id
            pos (Position): current position
            brute_pos (Position): BRUTE position

        Returns:
            None
        """
        distance_to_brute = self._distance(pos, brute_pos)
        ideal_support_distance = 60  # REDUCED from 90 to 60 - stay much closer

        if (
            distance_to_brute > ideal_support_distance + 15
        ):  # REDUCED tolerance from 30 to 15
            # Too far - get closer to BRUTE immediately
            self._smart_move_to(ent, pos, brute_pos)
        elif distance_to_brute < ideal_support_distance - 10:  # REDUCED from 20 to 10
            # Too close - maintain optimal distance
            self._move_to_support_distance(ent, pos, brute_pos, ideal_support_distance)
        else:
            # Perfect support position
            self._stop_movement(ent)

    def _move_to_support_distance(self, ent, pos, brute_pos, target_distance):
        """Move to a point at ``target_distance`` from the BRUTE.

        Args:
            ent (int): entity id
            pos (Position): current position
            brute_pos (Position): BRUTE position
            target_distance (float): desired distance from the BRUTE

        Returns:
            None
        """
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
        """Immediate GHAST-handling routine: focus, move and engage.

        GHASTs are the highest-priority threat. This method delegates to the
        focussed GHAST handling routine which sets the combat target and uses
        aggressive positioning to remove the GHAST quickly.

        Args:
            ent (int): entity id
            pos (Position): position
            attack (Attack): attack component
            team_id (int): team identifier
            ghast_target (tuple): (entity_id, Position)

        Returns:
            None
        """
        ghast_ent, ghast_pos = ghast_target

        # ALWAYS focus fire on GHAST - no exceptions, no base defense considerations
        # The best defense against GHAST is to kill it quickly
        self._focus_ghast(ent, pos, ghast_target, attack)

    def _defend_base_actively(self, ent, pos, team_id):
        """Actively defend the friendly base: engage highest threat or hold perimeter.

        Args:
            ent (int): entity id
            pos (Position): current position
            team_id (int): team identifier

        Returns:
            None
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
            # Force direct engagement: move straight to the attacker so defenders
            # do not stay idle in a corner. This allows units to enter the enemy's
            # attack range to defend the bastion aggressively.
            # We still set the combat target so firing logic works as usual.
            destination = Position(
                max(32, min(enemy_pos.x, 24 * 32 - 32)),
                max(32, min(enemy_pos.y, 24 * 32 - 32)),
            )
            self._smart_move_to(ent, pos, destination)
        else:
            # No immediate threats - maintain defensive perimeter
            self.movement_controller.position_defensively_near_base(ent, pos, team_id)

    def _position_for_base_defense(self, ent, pos, enemy_pos, base_pos):
        """Compute a defensible position between base and attacker and move.

        Args:
            ent (int): entity id
            pos (Position): current unit position
            enemy_pos (Position): attacker position
            base_pos (Position): friendly base position

        Returns:
            None
        """
        distance_to_enemy = self._distance(pos, enemy_pos)
        distance_to_base = self._distance(pos, base_pos)
        optimal_range = 100  # Aggressive defensive range
        # Allow units that are farther from the base to still move toward the
        # attacker to defend the bastion, but cap how far from the base they
        # may go when closing. This prevents distant units from staying idle
        # in a corner when the base is under attack.
        max_allowed_distance_from_base = 400

        if distance_to_enemy > optimal_range:
            # Close with enemy. Compute candidate move and ensure we don't
            # end up farther than max_allowed_distance_from_base from the base.
            direction_x = enemy_pos.x - pos.x
            direction_y = enemy_pos.y - pos.y
            length = (direction_x**2 + direction_y**2) ** 0.5

            if length > 0:
                move_distance = min(40, distance_to_enemy - optimal_range)
                direction_x = direction_x / length * move_distance
                direction_y = direction_y / length * move_distance

                new_x = pos.x + direction_x
                new_y = pos.y + direction_y

                # If moving there would place us too far from base, clamp to a point
                # on the vector from base to the candidate within allowed radius.
                test_distance_to_base = self._distance(Position(new_x, new_y), base_pos)
                if test_distance_to_base <= max_allowed_distance_from_base:
                    destination = Position(new_x, new_y)
                    self._smart_move_to(ent, pos, destination)
                else:
                    # Clamp the destination to max_allowed_distance_from_base from base
                    vec_x = new_x - base_pos.x
                    vec_y = new_y - base_pos.y
                    vec_len = (vec_x**2 + vec_y**2) ** 0.5
                    if vec_len > 0:
                        clamp_x = (
                            base_pos.x
                            + vec_x / vec_len * max_allowed_distance_from_base
                        )
                        clamp_y = (
                            base_pos.y
                            + vec_y / vec_len * max_allowed_distance_from_base
                        )
                        destination = Position(
                            max(32, min(clamp_x, 24 * 32 - 32)),
                            max(32, min(clamp_y, 24 * 32 - 32)),
                        )
                        self._smart_move_to(ent, pos, destination)
        elif distance_to_enemy < optimal_range * 0.6:
            # Too close - retreat toward base
            self._retreat_toward_base(ent, pos, enemy_pos, base_pos)
        else:
            # Good defensive position
            self._stop_movement(ent)

    def _get_fallback_base_position(self, team_id):
        """Return a fallback base position when no BASTION entity is present.

        Args:
            team_id (int): team identifier

        Returns:
            Position: a reasonable map coordinate for the team's base area
        """
        if team_id == 2:
            return Position(20 * 32, 20 * 32)
        else:
            return Position(4 * 32, 4 * 32)

    def _defend_base_actively(self, ent, pos, team_id):
        """Maintain defensive posture near base and engage nearby threats.

        This variant performs a proactive scan and uses positioning helpers
        to keep units near the bastion while allowing them to intercept
        attackers.

        Args:
            ent (int): entity id
            pos (Position): current position
            team_id (int): team identifier

        Returns:
            None
        """
        base_pos = self._find_friendly_base(
            team_id
        ) or self._get_fallback_base_position(team_id)

        # Use helper to find the most dangerous threat to our base
        closest_threat = self.base_defense.find_base_threat(pos, team_id)

        if closest_threat:
            # Engage the threat while keeping a defensive posture
            enemy_ent, enemy_pos, enemy_type = closest_threat
            self._set_combat_target(ent, enemy_ent)
            self._position_for_base_defense(ent, pos, enemy_pos, base_pos)
            return

        # No immediate threats: hold defensive perimeter and proactively scan
        # for any enemies within our attack capability and engage if found.
        self.movement_controller.position_defensively_near_base(ent, pos, team_id)

        # Proactive scan: if this unit has an Attack component, try to engage
        # any enemies that wander into effective range.
        if esper.has_component(ent, Attack):
            attack_comp = esper.component_for_entity(ent, Attack)
            enemies_in_range = self._find_enemies_in_range(
                ent, pos, attack_comp, team_id
            )
            if enemies_in_range:
                best = self.target_prioritizer.prioritize_targets(enemies_in_range)
                if best:
                    self._attack_enemy(ent, pos, best, attack_comp)

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
        """Return enemies within this unit's attack range.

        Args:
            ent (int): entity id of the caller
            pos (Position): caller position
            attack (Attack): attack component (provides range)
            team_id (int): caller team id

        Returns:
            list[tuple]: (entity_id, Position, EntityType) for each valid target
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
        """Return True if the given entity is alive (health > 0).

        Args:
            ent (int): entity id

        Returns:
            bool
        """
        if esper.has_component(ent, Health):
            health = esper.component_for_entity(ent, Health)
            return health.remaining > 0
        return True  # Assume alive if no health component

    def _move_closer_to_target(self, ent, pos, target_pos, optimal_range):
        """Advance toward ``target_pos`` while stopping at ``optimal_range``.

        Args:
            ent (int): entity id
            pos (Position): current position
            target_pos (Position): target position to approach
            optimal_range (float): desired stopping distance in pixels

        Returns:
            None
        """
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
        """Move back toward the friendly base while attempting to stay engaged.

        If a base position is available the unit will head directly to it; when
        no base is found a conservative fallback is applied.

        Args:
            ent (int): entity id
            pos (Position): current position
            enemy_pos (Position): position of the threat
            base_pos (Position|None): friendly base position if known

        Returns:
            None
        """
        # Move to the bastion position directly (place defender on the base)
        if base_pos:
            dest_x = max(32, min(base_pos.x, 24 * 32 - 32))
            dest_y = max(32, min(base_pos.y, 24 * 32 - 32))
            destination = Position(dest_x, dest_y)
            self._smart_move_to(ent, pos, destination)
        else:
            # Fallback to simple smart move to enemy's direction if no base found
            retreat_x = pos.x + (base_pos.x - enemy_pos.x) * 0.3 if base_pos else pos.x
            retreat_y = pos.y + (base_pos.y - enemy_pos.y) * 0.3 if base_pos else pos.y
            destination = Position(retreat_x, retreat_y)
            self._smart_move_to(ent, pos, destination)

    def _attack_enemy(self, ent, pos, enemy_info, attack):
        """Set target and position for effective crossbow engagement.

        The method assigns a Target component and attempts to keep the unit
        at an effective firing distance (a fraction of max range). It will
        either advance, hold, or perform a short retreat to achieve the
        desired engagement distance.

        Args:
            ent (int): entity id
            pos (Position): current position
            enemy_info (tuple): (entity_id, Position, entity_type)
            attack (Attack): attack component with range info

        Returns:
            None
        """
        enemy_id, enemy_pos, enemy_type = enemy_info
        distance = self._distance(pos, enemy_pos)

        # Set combat target
        self._set_combat_target(ent, enemy_id)

        # Execute optimal combat positioning
        optimal_range = attack.range * 24 * 0.6  # 60% of max range

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
        """Step back a short distance from ``enemy_pos`` to regain range.

        Args:
            ent (int): entity id
            pos (Position): current position
            enemy_pos (Position): enemy position

        Returns:
            None
        """
        # Reduce how far we retreat to avoid excessive fleeing; back off just enough
        # to regain optimal ranged distance but stay in the fight.
        retreat_x = pos.x + (pos.x - enemy_pos.x) * 0.3
        retreat_y = pos.y + (pos.y - enemy_pos.y) * 0.3

        # Clamp to map bounds
        retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
        retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

        destination = Position(retreat_x, retreat_y)
        self._smart_move_to(ent, pos, destination)

    def _count_ally_brutes(self, team_id):
        """Return the number of BRUTE units for the specified team.

        Args:
            team_id (int): team identifier

        Returns:
            int
        """
        count = 0
        for ent, (team, entity_type) in esper.get_components(Team, EntityType):
            if team.team_id == team_id and entity_type == EntityType.BRUTE:
                count += 1
        return count

    def _coordinate_brute_support(self, ent, pos, attack, team_id, ally_brutes):
        """Choose and reserve a BRUTE to support, then provide support.

        Uses AIMemory and per-tick counters to avoid oscillation between
        BRUTEs. If already assigned the function continues the existing
        support assignment.

        Args:
            ent (int): entity id
            pos (Position): current position
            attack (Attack): attack component
            team_id (int): team identifier
            ally_brutes (list): list of brute info dicts

        Returns:
            None
        """
        # Ensure AIMemory exists and read assignment
        if not esper.has_component(ent, AIMemory):
            esper.add_component(ent, AIMemory())

        memory = esper.component_for_entity(ent, AIMemory)

        # Compute current support levels once
        all_crossbowmen = self._get_all_allied_crossbowmen(team_id)
        for brute in ally_brutes:
            brute["supporting_crossbowmen"] = self._count_crossbowmen_supporting_brute(
                brute["position"], all_crossbowmen
            )

        # If we already have an assigned brute and it's still valid, keep it
        if memory.assigned_brute_id:
            assigned = next(
                (b for b in ally_brutes if b.get("entity") == memory.assigned_brute_id),
                None,
            )
            if assigned:
                # Ensure assignment count reflects this reserved support
                self._brute_assignment_counts[memory.assigned_brute_id] = (
                    self._brute_assignment_counts.get(memory.assigned_brute_id, 0) + 1
                )
                # Continue providing support to the assigned brute
                self._provide_dedicated_brute_support(
                    ent, pos, attack, team_id, assigned
                )
                return
            else:
                # Assigned brute no longer valid (dead/missing) -> clear assignment
                memory.assigned_brute_id = None
                memory.assignment_active = False

        # Choose the brute with minimal effective support (existing assignments + current supporters)
        best = None
        best_score = None
        for brute in ally_brutes:
            entity_id = brute.get("entity")
            current_assigned = self._brute_assignment_counts.get(entity_id, 0)
            supporting = brute.get("supporting_crossbowmen", 0)
            effective = current_assigned + supporting
            # tie-breaker: distance to this crossbowman
            dist = self._distance(pos, brute.get("position"))
            score = (effective, dist)
            if best is None or score < best_score:
                best = brute
                best_score = score

        if best:
            # Reserve this brute for this arbalétrier to avoid oscillation
            chosen_id = best.get("entity")
            memory.assigned_brute_id = chosen_id
            memory.assignment_active = True
            # Increment global assignment count so next units consider this reservation
            self._brute_assignment_counts[chosen_id] = (
                self._brute_assignment_counts.get(chosen_id, 0) + 1
            )
            self._provide_dedicated_brute_support(ent, pos, attack, team_id, best)
            return

        # Fallback: support nearest BRUTE if none chosen above
        if ally_brutes:
            nearest_brute = min(
                ally_brutes, key=lambda b: self._distance(pos, b["position"])
            )
            memory.assigned_brute_id = nearest_brute.get("entity")
            memory.assignment_active = True
            self._brute_assignment_counts[nearest_brute.get("entity")] = (
                self._brute_assignment_counts.get(nearest_brute.get("entity"), 0) + 1
            )
            self._provide_dedicated_brute_support(
                ent, pos, attack, team_id, nearest_brute
            )

    def _get_all_allied_crossbowmen(self, team_id):
        """Return a list of all allied crossbowmen with positions.

        Args:
            team_id (int): team identifier

        Returns:
            list[dict]: each dict contains 'entity' and 'position'
        """
        crossbowmen = []
        for crossbow_ent, (team, entity_type, crossbow_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if team.team_id == team_id and entity_type == EntityType.CROSSBOWMAN:
                crossbowmen.append({"entity": crossbow_ent, "position": crossbow_pos})
        return crossbowmen

    def _count_crossbowmen_supporting_brute(self, brute_pos, all_crossbowmen):
        """Count crossbowmen within a close radius to consider as supporters.

        Args:
            brute_pos (Position): BRUTE position
            all_crossbowmen (list): list from _get_all_allied_crossbowmen

        Returns:
            int
        """
        support_count = 0
        for crossbow in all_crossbowmen:
            distance = self._distance(crossbow["position"], brute_pos)
            if distance <= 80:  # REDUCED from 150 to 80 - much tighter support range
                support_count += 1
        return support_count

    def _provide_dedicated_brute_support(self, ent, pos, attack, team_id, brute_info):
        """Execute dedicated support behaviour for an assigned BRUTE.

        If the BRUTE is in combat, this will select and engage threats; if
        not, the unit will maintain formation with the BRUTE.

        Args:
            ent (int): entity id
            pos (Position): current position
            attack (Attack): attack component
            team_id (int): team identifier
            brute_info (dict): BRUTE metadata

        Returns:
            None
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
        """Maintain formation while following a moving BRUTE.

        Args:
            ent (int): entity id
            pos (Position): current position
            brute_pos (Position): BRUTE position

        Returns:
            None
        """
        distance_to_brute = self._distance(pos, brute_pos)
        optimal_follow_distance = 50  # REDUCED from 80 to 50 - stay much closer

        if distance_to_brute > optimal_follow_distance + 15:  # REDUCED from 30 to 15
            # Too far - close formation immediately
            self._smart_move_to(ent, pos, brute_pos)
        elif distance_to_brute < optimal_follow_distance - 10:  # REDUCED from 20 to 10
            # Too close - maintain optimal support distance
            self._move_to_support_distance(ent, pos, brute_pos, optimal_follow_distance)
        else:
            # Perfect formation - ready for combat
            self._stop_movement(ent)

    def _active_combat_support(self, ent, pos, attack, team_id, brute_pos):
        """Search for and engage threats that are endangering a BRUTE.

        Args:
            ent (int): entity id
            pos (Position): current position
            attack (Attack): attack component
            team_id (int): team identifier
            brute_pos (Position): BRUTE position

        Returns:
            None
        """
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
        """Return a numeric priority for a candidate target when supporting a BRUTE.

        Args:
            target_type (EntityType): unit type of the candidate
            distance_to_brute (float): proximity to the BRUTE
            distance_to_self (float): proximity to this unit

        Returns:
            float: higher value = higher priority
        """
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
        """Coordinate an attack when the team has local superiority and no BRUTEs need support.

        This routine focuses on base attacks first, then groups of enemies and
        finally moves toward enemy territory.

        Args:
            ent (int): entity id
            pos (Position): current position
            attack (Attack): attack component
            team_id (int): team identifier

        Returns:
            None
        """
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
        """Return the number of allied crossbowmen including self.

        Args:
            current_ent (int): entity id of caller
            team_id (int): team identifier

        Returns:
            int
        """
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
        """Return the number of enemy units within ``range_distance`` of ``pos``.

        Args:
            pos (Position): reference position
            team_id (int): own team id
            range_distance (float): radius in pixels

        Returns:
            int
        """
        count = 0
        for ent, (enemy_pos, enemy_team) in esper.get_components(Position, Team):
            if enemy_team.team_id != team_id:
                distance = self._distance(pos, enemy_pos)
                if distance <= range_distance:
                    count += 1
        return count

    def _calculate_ally_force(self, current_ent, team_id, pos, range_distance=400):
        """Estimate allied force nearby using simple point values.

        Point values (tunable): BRUTE=3, CROSSBOWMAN=5, GHAST=8.

        Args:
            current_ent (int): entity id of the caller (unused)
            team_id (int): team identifier
            pos (Position): reference position
            range_distance (float): radius to include allies

        Returns:
            int: summed force points
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
        """Estimate enemy force nearby using the same point scale as allies.

        Args:
            team_id (int): own team id (enemies are the other team)
            pos (Position): reference position
            range_distance (float): radius in pixels

        Returns:
            int
        """
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
        """Return the closest enemy GHAST within ``range_distance``.

        Args:
            pos (Position): reference position
            team_id (int): own team id
            range_distance (float): search radius

        Returns:
            tuple|None: (entity_id, Position) or None
        """
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

    def _count_defenders_near_base(self, team_id):
        """Return how many allied crossbowmen are positioned close to the base.

        Args:
            team_id (int): team identifier

        Returns:
            int
        """
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
        """Specialized defense routine for intercepting a GHAST approaching the base.

        Args:
            ent (int): entity id
            pos (Position): current position
            attack (Attack): attack component
            team_id (int): team identifier
            ghast_target (tuple): (entity_id, Position)

        Returns:
            None
        """
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
        """Aggressively engage a GHAST: set it as target and close to optimal range.

        Args:
            ent (int): entity id
            pos (Position): current position
            ghast_target (tuple): (entity_id, Position)
            attack (Attack): attack component

        Returns:
            None
        """
        ghast_ent, ghast_pos = ghast_target
        distance = self._distance(pos, ghast_pos)

        # Set GHAST as primary target with highest priority
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(ghast_ent))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = ghast_ent

        # Maintain aggressive range for GHAST combat - get closer for better accuracy
        optimal_range = (
            attack.range * 24 * 0.85
        )  # 85% of max range - closer than before
        min_safe_distance = attack.range * 24 * 0.5  # Don't get too close to GHAST

        if distance > optimal_range:
            # Too far - IMMEDIATELY move toward GHAST, no hesitation
            self._smart_move_to(ent, pos, ghast_pos)
        elif distance < min_safe_distance:
            # Too close to GHAST - back away to safer distance but keep firing
            retreat_x = pos.x + (pos.x - ghast_pos.x) * 0.4  # Stronger retreat
            retreat_y = pos.y + (pos.y - ghast_pos.y) * 0.4

            # Clamp to map bounds
            retreat_x = max(32, min(retreat_x, 24 * 32 - 32))
            retreat_y = max(32, min(retreat_y, 24 * 32 - 32))

            destination = Position(retreat_x, retreat_y)
            self._smart_move_to(ent, pos, destination)
        else:
            # Perfect GHAST killing range - stop and focus fire
            self._stop_movement(ent)

    def _count_brutes_in_combat(self, team_id):
        """Return the number of allied BRUTEs that currently have nearby enemies.

        Args:
            team_id (int): team identifier

        Returns:
            int
        """
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
        """Return up to ``count`` crossbowman entity ids closest to ``target_pos``.

        Args:
            target_pos (Position): reference position
            team_id (int): team identifier
            count (int): maximum number of entities to return

        Returns:
            list[int]
        """
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
        """Move to a defensive location (base or spawn corner) when outnumbered.

        Args:
            ent (int): entity id
            pos (Position): current position
            team_id (int): team identifier

        Returns:
            None
        """
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
        """Hold a defensive position near the friendly base and engage threats.

        This routine searches for enemies close to the base, selects the most
        relevant threat and either positions to engage or holds the defensive
        perimeter.

        Args:
            ent (int): entity id
            pos (Position): current position
            team_id (int): team identifier

        Returns:
            None
        """
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
        """Move to and attack the enemy base or fallback spawn area.

        Args:
            ent (int): entity id
            pos (Position): current position
            team_id (int): team identifier

        Returns:
            None
        """
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
        """Move the unit toward the map center using safe movement helpers.

        Args:
            ent (int): entity id
            pos (Position): current position

        Returns:
            None
        """
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
        """Emit a move event to travel toward the specified point.

        Ensures the entity has a Velocity component then emits an
        EventMoveTo which the movement system will act upon.

        Args:
            ent (int): entity id
            pos (Position): current position (unused here)
            target_x (float): destination x-coordinate
            target_y (float): destination y-coordinate

        Returns:
            None
        """
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
        """Calculate Manhattan distance between two positions."""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)
