import math, random
from time import sleep

import esper
from ai.ai_state import AiState
from ai.behavior_tree import Status
from ai.pathfinding import astar
from components.ai_controller import AIController
from components.base.health import Health
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
from components.gameplay.attack import Attack
from components.gameplay.target import Target
from core.accessors import get_config, get_debugger, get_event_bus, get_map
from core.ecs.component import Component
from core.game.player import Player
from enums.config_key import ConfigKey
from enums.entity.animation import Animation
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType
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

    state.target = None
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
    pos: Position = state.pos
    atk: Attack = state.atk

    target_id = state.target.target_entity_id
    if not target_id or not esper.entity_exists(target_id):
        state.target.target_entity_id = None
        return Status.FAILURE

    if state.in_attack_range:
        get_debugger().log(f"{state.entity} > Attacking target {target_id}")
        return Status.RUNNING
    else:
        get_debugger().log(f"{state.entity} > Moving to attack target {target_id}")
        target_pos: Position = esper.component_for_entity(target_id, Position)
        return move_to(ent, (target_pos.x, target_pos.y), force=True)


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

    # Avance le long du path
    dx = state.destination[0] - pos.x
    dy = state.destination[1] - pos.y
    dist = math.hypot(dx, dy)
    if dist < 32:
        get_debugger().log(f"{ent} > Reached waypoint {state.destination}.")
        state.path.pop(0)
        if state.path:
            state.destination = state.path[0]
        else:
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
    get_debugger().log("Protecting ally...")
    ctrl = esper.component_for_entity(ent, AIController)
    atk = esper.component_for_entity(ent, Attack)
    pos = esper.component_for_entity(ent, Position)
    team = esper.component_for_entity(ent, Team)

    # Trouve les ennemis proches de l’allié protégé
    ally_id = ctrl.ally_target
    if ally_id is None or not esper.has_component(ally_id, Position):
        return Status.FAILURE

    ally_pos = esper.component_for_entity(ally_id, Position)
    enemies_in_range = []

    for other, (enemy_pos, enemy_team) in esper.get_components(Position, Team):
        if enemy_team.team_id == team.team_id:
            continue
        dx = enemy_pos.x - ally_pos.x
        dy = enemy_pos.y - ally_pos.y
        if dx * dx + dy * dy <= (atk.range * 2) ** 2:
            enemies_in_range.append((other, dx * dx + dy * dy))

    if not enemies_in_range:
        return Status.SUCCESS  # plus rien à protéger

    # Attaque l’ennemi le plus proche
    enemies_in_range.sort(key=lambda e: e[1])
    target_enemy = enemies_in_range[0][0]
    ctrl.target = target_enemy

    return attack_target(ent)


def move_to_ally(ent: int) -> Status:
    ctrl = esper.component_for_entity(ent, AIController)
    pos = esper.component_for_entity(ent, Position)

    if not ctrl.target_pos:
        return Status.FAILURE

    dx = ctrl.target_pos[0] - pos.x
    dy = ctrl.target_pos[1] - pos.y
    if dx * dx + dy * dy < (get_config().get(ConfigKey.TILE_SIZE.value) * 2) ** 2:
        return Status.SUCCESS

    move_to(ent, ctrl.target_pos)
    return Status.RUNNING


# def has_enemy_bastion(ent):
#    team : Team = esper.component_for_entity(ent,Team)
#
#    from core.services import Services
#    enemy : Player = Services.player_manager.get_enemy_player(team.team_id)
#
#    bastion : int = enemy.bastion
#
#    health : Health = esper.component_for_entity(bastion,Health)
#
#    if health > 0:
#        return True
#    else:
#        return False
