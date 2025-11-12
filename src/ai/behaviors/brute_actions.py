import math, random
from time import sleep

import esper
from ai.ai_state import AiState
from ai.behavior_tree import Status
from ai.pathfinding import astar
from components.base.cost import Cost
from components.base.health import Health
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
from components.case import Case
from components.gameplay.attack import Attack
from components.gameplay.target import Target
from core.accessors import (
    get_config,
    get_debugger,
    get_event_bus,
    get_map,
    get_player_manager,
    get_player_move_system,
)
from core.ecs.component import Component
from core.game.player import Player
from enums.case_type import CaseType
from enums.config_key import ConfigKey
from enums.entity.animation import Animation
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType
from events.attack_event import AttackEvent
from events.death_event import DeathEvent
from events.event_move import EventMoveTo
from events.stop_event import StopEvent


def perform_attack(attacker_id: int, target_id: int):
    """
    Performs an attack from one entity to another.

    Emits an `AttackEvent` on the event bus and logs the attack in the debugger.

    Args:
        attacker_id (int): ID of the attacking entity.
        target_id (int): ID of the target entity.
    """
    atk = esper.component_for_entity(attacker_id, Attack)

    damage = atk.damage
    get_event_bus().emit(AttackEvent(attacker_id, target_id))

    get_debugger().log(f"{attacker_id} > Attack {target_id} for {damage} dmg.")


def ally_in_danger(state: AiState) -> bool:
    """
    UNUSED
    Determines whether an ally is in danger and requires assistance.

    This function evaluates the AI state to see if a weak ally nearby
    is in urgent danger based on distance, alert level, and the ally’s danger score.
    The entity may decide to help depending on combat conditions.

    Args:
        state (AiState): The AI state of the entity evaluating the situation.

    Returns:
        bool: True if an ally needs immediate protection, False otherwise.
    """

    if not state.weakness_ally or state.weakness_ally not in state.allies:
        return False

    get_debugger().log(f"{state.entity} > Alert level : {state.alert_level}")

    if state.alert_level < 0.2:
        return False

    dist_to_ally = state.allies[state.weakness_ally][1]
    tile_size = get_config().get(ConfigKey.TILE_SIZE.value)

    _, _, _, danger_score = state.allies[state.weakness_ally]
    # Check if protection is urgent
    get_debugger().log(
        f"{state.entity} > Danger score for {state.weakness_ally} : {danger_score}"
    )
    urgent = danger_score > 0.3

    # Protect only if entity is not here
    if dist_to_ally <= tile_size * 2:
        # get_debugger().log(f"{state.entity} > Too near to protect")
        return False

    # If danger is not urgent , check if fight is critical
    if not urgent and state.in_combat and state.nearest_enemy:

        get_debugger().log(f"{state.entity} > Check for help")
        enemy_id, _, _ = state.nearest_enemy
        enemy_health = esper.component_for_entity(enemy_id, Health)
        enemy_ratio = enemy_health.remaining / enemy_health.full
        # Enemy almost dead
        if enemy_ratio < 0.5:
            get_debugger().log(f"{state.entity} > Continue fighting")
            return False
    if urgent:
        get_debugger().log(f"{state.entity} > Go help {state.weakness_ally}")
    return urgent


class BaseAction:
    """
    Abstract base class for all AI actions.

    Each action implements an `execute` method that performs a specific behavior
    such as attacking, moving, retreating, or protecting.
    """

    def __init__(self, ai_state: AiState):
        """
        Initializes an AI action.

        Args:
            ai_state (AiState): The AI state of the controlled entity.
        """
        self.ai_state = ai_state

    def execute(self) -> Status:
        """
        Executes the behavior associated with this action.

        Returns:
            Status: The result of the action (SUCCESS, FAILURE, or RUNNING).
        """
        raise NotImplementedError


class RetreatAction(BaseAction):
    """
    Makes the entity retreat from a dangerous area by moving away
    from the closest enemy.
    """

    def execute(self) -> Status:
        """
        Executes the retreat behavior.

        The entity retreats in the opposite direction of its nearest enemy,
        clamping to map limits and avoiding obstacles or inaccessible areas.
        """
        state = self.ai_state
        get_debugger().log(
            f"{state.entity} > Retreat {state.action_weights} "
            f"{state._emotions} {state.alert_level} {state.enemies} {state.under_attack}"
        )

        if not state.enemies:
            return Status.FAILURE

        nearest_enemy = state.nearest_enemy
        if not nearest_enemy:
            return Status.FAILURE

        enemy_pos = nearest_enemy[1]
        dx = state.pos.x - enemy_pos.x
        dy = state.pos.y - enemy_pos.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return Status.FAILURE

        tile_size = state._tile_size
        map_data: list[list[Case]] = get_map().tab
        map_w = len(map_data[0])
        map_h = len(map_data)

        flee_x = state.pos.x + (dx / dist) * tile_size * 3
        flee_y = state.pos.y + (dy / dist) * tile_size * 3

        flee_x = max(0, min(flee_x, (map_w - 1) * tile_size))
        flee_y = max(0, min(flee_y, (map_h - 1) * tile_size))

        tx = int(flee_x // tile_size)
        ty = int(flee_y // tile_size)

        # Tile exist
        def is_valid_tile(x, y):
            return 0 <= x < map_w and 0 <= y < map_h

        # Check if it's walkable tile
        def is_walkable_tile(x, y):
            return is_valid_tile(x, y) and map_data[y][x].type == CaseType.LAVA

        # If target tile didn't walkable try another near
        if not is_walkable_tile(tx, ty):
            best_pos = None
            best_score = -1.0

            for ox in range(-2, 3):
                for oy in range(-2, 3):
                    nx = tx + ox
                    ny = ty + oy
                    if not is_walkable_tile(nx, ny):
                        continue

                    nx_pos = nx * tile_size + tile_size / 2
                    ny_pos = ny * tile_size + tile_size / 2
                    d = math.hypot(nx_pos - enemy_pos.x, ny_pos - enemy_pos.y)
                    if d > best_score:
                        best_score = d
                        best_pos = (nx_pos, ny_pos)

            if not best_pos:
                return Status.FAILURE

            flee_x, flee_y = best_pos

        return MovementManager.move_to(state, (flee_x, flee_y))


class ProtectAction(BaseAction):
    """
    Directs the entity to protect a nearby ally that is in danger.
    """

    def execute(self):
        """
        Executes the protection behavior.

        The entity moves toward the endangered ally if too far away.
        If already close, it succeeds without moving.

        Returns:
            Status: RUNNING while moving,
                    SUCCESS if already close,
                    FAILURE if no valid ally found or too near to protect.
        """
        state = self.ai_state

        get_debugger().log(
            f"{state.entity} > Protect {state.action_weights} {state._emotions} {state.alert_level} {state.enemies} {state.under_attack}"
        )
        if state.weakness_ally is None or state.weakness_ally not in state.allies:
            return Status.FAILURE

        get_debugger().log(
            f"{state.entity} > Moving to protect ally {state.weakness_ally}. {state.action_weights}, {state._emotions}"
        )

        ally_pos = state.allies[state.weakness_ally][0]
        dist_to_ally = state.allies[state.weakness_ally][1]
        tile_size = get_config().get(ConfigKey.TILE_SIZE.value)

        if dist_to_ally > tile_size * 2:
            return MovementManager.move_to(state, (ally_pos.x, ally_pos.y))
        # if too near, to stop protection move
        return Status.FAILURE


class AttackAction(BaseAction):
    """
    Controls the attack behavior of an entity.

    The entity either attacks if the target is in range or moves closer to it.
    """

    def execute(self) -> Status:
        """
        Executes the combat behavior for the entity.

        - If the current target is within attack range, the entity attacks.
        - If the target is too far, the entity moves toward it.

        Returns:
            Status: RUNNING while attacking or moving,
                    FAILURE if no valid target is available,
                    SUCCESS after a successful attack.
        """
        state = self.ai_state

        get_debugger().log(
            f"{state.entity} > Attack {state.action_weights} {state._emotions} {state.alert_level} {state.enemies} {state.under_attack}"
        )
        atk: Attack = state.atk

        if not state.nearest_enemy or state.nearest_enemy[0] not in state.enemies:
            return Status.FAILURE

        target_id = state.nearest_enemy[0]
        target_pos, dist = state.enemies[target_id]

        # Check distance to target
        if dist < atk.range:

            # Stop moving
            MovementManager.stop(state)

            # Check attack cooldown
            if not state.can_attack:
                return Status.RUNNING

            perform_attack(state.entity, target_id)
            state.can_attack = False
            state.atk.last_attack = 0
            return Status.SUCCESS

        # Go to target if too far
        return MovementManager.move_to(state, (target_pos.x, target_pos.y))


class TargetObjective(BaseAction):
    """
    Makes the entity move toward a strategic objective,
    typically the enemy base position.
    """

    def execute(self):
        """
        Executes the objective targeting behavior.

        Moves the entity toward the stored enemy base position if it exists.

        Returns:
            Status: RUNNING while moving,
                    FAILURE if no base position is known.
        """
        state = self.ai_state

        get_debugger().log(f"{state.entity} > Target : {state.enemy_base_pos}")
        if state.enemy_base_pos:
            base_pos = (state.enemy_base_pos.x, state.enemy_base_pos.y)
            tile_size = state._tile_size
            random_pos: list[tuple[int, int]] = [
                base_pos,
                (base_pos[0] + tile_size, base_pos[1]),
                (base_pos[0] + tile_size, base_pos[1] + tile_size),
                (base_pos[0], base_pos[1] + tile_size),
            ]
            rd = random.randint(0, 3)
            state.destination = random_pos[rd]
            state.path = []
            return MovementManager.move_to(state, base_pos, True)
        return Status.FAILURE


class WanderAction(BaseAction):
    """
    Causes an idle entity to wander randomly around the map.
    """

    def execute(self):
        """
        Causes the entity to wander randomly when idle.

        If the entity has no current path, it selects a random nearby position
        and moves toward it. Otherwise, it continues along its current path.

        Returns:
            Status: RUNNING while moving,
                    SUCCESS when idle or path completed.
        """
        state = self.ai_state

        get_debugger().log(f"{state.entity} > Wander")

        if not state.path or not state.destination:
            # get_debugger().log(f"{state.entity} > Wandering to a new random location.")
            tile_size = get_config().get(ConfigKey.TILE_SIZE.value)
            map_w = len(get_map().tab[0]) * tile_size
            map_h = len(get_map().tab) * tile_size
            dest_x = max(0, min(map_w, state.pos.x + random.randint(-500, 500)))
            dest_y = max(0, min(map_h, state.pos.y + random.randint(-500, 500)))
            return MovementManager.move_to(state, (dest_x, dest_y))

        # get_debugger().log(
        #    f"{state.entity} > Continuing to wander toward {state.destination}, current : {state.pos.x}, {state.pos.y}."
        # )

        return MovementManager.move_to(state, state.destination)


class MovementManager:
    """
    Manages entity movement, pathfinding, and navigation.
    Provides static methods for moving entities toward a goal or stopping them.
    """

    @staticmethod
    def move_to(state: AiState, target: tuple[int, int], force: bool = False) -> Status:
        """
        Moves an entity toward a target position using A* pathfinding.

        Recalculates the path if:
          - No current path exists, or
          - `force` is True and the target has changed significantly.

        Args:
            state (AiState): The current AI state of the entity.
            target (tuple[int, int]): Destination coordinates (x, y).
            force (bool, optional): Whether to force path recalculation. Defaults to False.

        Returns:
            Status:
                - RUNNING while following a path,
                - SUCCESS when the destination is reached,
                - FAILURE if no valid path could be found.
        """

        pos = esper.component_for_entity(state.entity, Position)
        vel = esper.component_for_entity(state.entity, Velocity)

        if not state.path or state.destination != target or force:

            path = astar(pos, target, get_map().tab)
            if not path or len(path) < 2:
                state.path = []
                state.destination = None
                return Status.FAILURE

            state.path = [(int(x), int(y)) for x, y in path[1:]]
            state.destination = state.path[0]
            get_event_bus().emit(
                EventMoveTo(state.entity, state.destination[0], state.destination[1])
            )
        dx = state.destination[0] - pos.x
        dy = state.destination[1] - pos.y
        dist = math.hypot(dx, dy)

        if dist < 16:
            get_debugger().log(
                f"{state.entity} > Reached waypoint {state.destination}."
            )
            state.path.pop(0)

            if state.path:
                state.destination = state.path[0]
            else:
                del get_player_move_system().target[state.entity]
                vel.x = 0
                vel.y = 0
                state.destination = None
                get_event_bus().emit(StopEvent(state.entity))
                return Status.SUCCESS
        else:

            vel.x = (dx / dist) * vel.speed
            vel.y = (dy / dist) * vel.speed

        return Status.RUNNING

    @staticmethod
    def stop(state: AiState):
        """
        Immediately stops entity movement.

        Resets velocity, clears destination and path, and ensures the entity
        no longer continues to move during the next update cycle.

        Args:
            state (AiState): The AI state of the entity to stop.
        """
        vel: Velocity = esper.component_for_entity(state.entity, Velocity)
        vel.x = 0
        vel.y = 0

        state.destination = None
        state.path = []


class DefendBaseAction(BaseAction):
    """Défend la base alliée lorsqu’elle est attaquée."""

    def execute(self) -> Status:
        state = self.ai_state
        base_pos = state.ally_base_pos
        tile_size = get_config().get(ConfigKey.TILE_SIZE.value)

        get_debugger().log(
            f"{state.entity} > Defend base {state.action_weights} {state._emotions}"
        )

        dist_to_base = math.hypot(base_pos.x - state.pos.x, base_pos.y - state.pos.y)
        if dist_to_base > tile_size * 8:
            return Status.FAILURE  # too far to defend

        # Check enemie presence near the base
        enemies_near_base = [
            ent_id
            for ent_id, dist in state.world_perception.neighbors.get(
                state.ally_base, {}
            ).items()
            if state.world_perception.teams[ent_id].team_id != state.team
            and dist <= tile_size * 8
        ]

        if not enemies_near_base:
            # Any danger so defend is not necessary
            return Status.FAILURE

        # if an enemy is near attack it
        if state.nearest_enemy and state.nearest_enemy[2] <= state.atk.range:
            get_debugger().log(f"{state.entity} > Attacking near base!")
            return AttackAction(state).execute()

        # else go to defend
        if dist_to_base > tile_size * 2:
            get_debugger().log(f"{state.entity} > Moving to defend base at {base_pos}")
            return MovementManager.move_to(state, (base_pos.x, base_pos.y))

        return Status.RUNNING
