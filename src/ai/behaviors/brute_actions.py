import math, random
from time import sleep

import esper
from ai.ai_state import AiState
from ai.behavior_tree import Status
from ai.pathfinding import astar
from components.ai_controller import AIController
from components.base.cost import Cost
from components.base.health import Health
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
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
from enums.config_key import ConfigKey
from enums.entity.animation import Animation
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType
from events.attack_event import AttackEvent
from events.death_event import DeathEvent
from events.event_move import EventMoveTo


def enemy_near(ent) -> bool:
    """
    Detects if an enemy is within the entity's vision range.

    The nearest visible enemy from an opposing team that matches
    the allowed target types will be assigned to `ctrl.target`.

    Args:
        ent (int): The entity ID to check for nearby enemies.

    Returns:
        bool: True if an enemy is found within vision range, False otherwise.
    """
    ctrl: AIController = esper.component_for_entity(ent, AIController)

    state = ctrl.state

    if state.nearest_enemy:
        state.target.target_entity_id = state.nearest_enemy[0]
        return True

    state.target.target_entity_id = None
    return False


def attack_target(ent):
    """
    Executes combat behavior for the entity.

    - If the current target is within attack range, the entity attacks.
    - If the target is too far, the entity moves toward it.

    Args:
        ent (int): The entity ID executing the attack behavior.

    Returns:
        Status: RUNNING while attacking or moving,
                FAILURE if no valid target is available.
    """
    ctrl: AIController = esper.component_for_entity(ent, AIController)

    state: AiState = ctrl.state
    atk: Attack = state.atk

    if not state.nearest_enemy or state.nearest_enemy[0] not in state.ennemies:
        return Status.FAILURE

    target_id = state.nearest_enemy[0]
    target_pos, dist = state.ennemies[target_id]

    # Check distance to target
    if dist <= atk.range:

        # Stop moving
        stop(ent)

        # Check attack cooldown
        if not state.can_attack:
            return Status.RUNNING

        perform_attack(ent, target_id)
        state.can_attack = False
        state.atk.last_attack = 0
        return Status.SUCCESS

    # Go to target if too far
    return move_to(ent, (target_pos.x, target_pos.y))


def stop(ent: int):
    """
    Stop entity movement, reset velocity , destination and path

    Args:
        ent (int) : The entity ID to stop
    """
    vel: Velocity = esper.component_for_entity(ent, Velocity)
    vel.x = 0
    vel.y = 0

    ctrl: AIController = esper.component_for_entity(ent, AIController)
    state: AiState = ctrl.state
    state.destination = None
    state.path = []


def perform_attack(attacker_id: int, target_id: int):
    atk = esper.component_for_entity(attacker_id, Attack)

    damage = atk.damage
    get_event_bus().emit(AttackEvent(attacker_id, target_id))

    get_debugger().log(f"{attacker_id} attacks {target_id} for {damage} dmg.")


def wander(ent):
    """
    Causes the entity to wander randomly when idle.

    If the entity has no current path, it selects a random nearby position
    and moves toward it. Otherwise, it continues along its current path.

    Args:
        ent (int): The entity ID performing the wandering behavior.

    Returns:
        Status: RUNNING while moving,
                SUCCESS when idle or path completed.
    """

    ctrl: AIController = esper.component_for_entity(ent, AIController)
    state = ctrl.state

    if not state.path or not state.destination:
        get_debugger().log(f"{ent} > Wandering to a new random location.")
        tile_size = get_config().get(ConfigKey.TILE_SIZE.value)
        map_w = len(get_map().tab[0]) * tile_size
        map_h = len(get_map().tab) * tile_size
        dest_x = max(0, min(map_w, state.pos.x + random.randint(-500, 500)))
        dest_y = max(0, min(map_h, state.pos.y + random.randint(-500, 500)))
        return move_to(ent, (dest_x, dest_y))

    get_debugger().log(
        f"{ent} > Continuing to wander toward {state.destination}, current : {state.pos.x}, {state.pos.y}."
    )

    return move_to(ent, state.destination)


def move_to(ent: int, target: tuple[int, int], force: bool = False) -> Status:
    """
    Moves an entity toward a target position using A* pathfinding.

    Automatically recalculates the path if:
    - No current path exists, or
    - `force` is True and the target has significantly changed.

    Args:
        ent (int): The entity ID to move.
        target (tuple[int,int]): The desired destination.
        force (bool, optional): Whether to force a path recalculation. Defaults to False.

    Returns:
        Status:
            - RUNNING while following a path,
            - SUCCESS when destination is reached,
            - FAILURE if no path could be found.
    """
    pos = esper.component_for_entity(ent, Position)
    vel = esper.component_for_entity(ent, Velocity)
    ctrl = esper.component_for_entity(ent, AIController)

    state = ctrl.state

    if not state.path or state.destination != target or force:
        path = astar(pos, target, get_map().tab)
        if not path or len(path) < 2:
            state.path = []
            state.destination = None
            return Status.FAILURE
        state.path = [(int(x), int(y)) for x, y in path[1:]]
        state.destination = state.path[0]

    dx = state.destination[0] - pos.x
    dy = state.destination[1] - pos.y
    dist = math.hypot(dx, dy)

    if dist < 16:
        get_debugger().log(f"{ent} > Reached waypoint {state.destination}.")
        state.path.pop(0)

        if state.path:
            state.destination = state.path[0]
        else:
            del get_player_move_system().target[state.entity]
            vel.x = 0
            vel.y = 0
            state.destination = None
            return Status.SUCCESS
    else:

        vel.x = (dx / dist) * vel.speed
        vel.y = (dy / dist) * vel.speed
        get_event_bus().emit(
            EventMoveTo(ent, state.destination[0], state.destination[1])
        )
    return Status.RUNNING


def ally_near(ent: int) -> bool:
    if not esper.has_component(ent, AIController):
        return False

    ctrl = esper.component_for_entity(ent, AIController)
    pos = esper.component_for_entity(ent, Position)
    team = esper.component_for_entity(ent, Team)
    entity_type = esper.component_for_entity(ent, EntityType)

    best_ally_id = None
    best_score = float("-inf")

    for other, (
        ally_pos,
        ally_team,
        ally_health,
        ally_entity_type,
    ) in esper.get_components(Position, Team, Health, EntityType):
        if (
            other == ent
            or ally_team.team_id != team.team_id
            or entity_type == ally_entity_type
        ):
            continue

        dx, dy = ally_pos.x - pos.x, ally_pos.y - pos.y
        dist_sq = dx * dx + dy * dy
        if dist_sq > ctrl.view_range**2:
            continue

        # Score basé sur santé basse + proximité
        hp_ratio = ally_health.remaining / max(1, ally_health.full)
        score = (1 - hp_ratio) * 2 - dist_sq / (ctrl.view_range**2)

        if score > best_score:
            best_score = score
            best_ally_id = other

    if best_ally_id is not None:
        best_ally_pos = esper.component_for_entity(best_ally_id, Position)
        ctrl.target_pos = (best_ally_pos.x, best_ally_pos.y)
        ctrl.ally_target = best_ally_id
        return True

    ctrl.target_pos = ctrl.target = None
    return False


def protect_ally(ent: int) -> Status:
    ctrl = esper.component_for_entity(ent, AIController)
    state = ctrl.state

    if state.weakness_ally is None or state.weakness_ally not in state.allies:
        return Status.FAILURE

    get_debugger().log(f"{ent} > Moving to protect ally {state.weakness_ally}.")

    ally_pos = state.allies[state.weakness_ally][0]
    dist_to_ally = state.allies[state.weakness_ally][1]
    tile_size = get_config().get(ConfigKey.TILE_SIZE.value)

    if dist_to_ally > tile_size * 1.5:
        return move_to(ent, (ally_pos.x, ally_pos.y))

    return Status.SUCCESS
