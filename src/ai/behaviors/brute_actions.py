import math, random
from time import sleep

import esper
from ai.behavior_tree import Status
from ai.pathfinding import astar
from components.ai_controller import AIController
from components.base.health import Health
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
from components.gameplay.attack import Attack
from components.gameplay.target import Target
from core.ecs.component import Component
from core.game.player import Player
from enums.entity.animation import Animation
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType


def enemy_near(ent):
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
    pos: Position = esper.component_for_entity(ent, Position)
    team: Team = esper.component_for_entity(ent, Team)
    target: Target = esper.component_for_entity(ent, Target)

    from core.services import Services

    vision_range: float = Services.config.get("tile_size") * 4

    nearest_enemy: int = None
    nearest_dist_sq: float = float("inf")

    for other, (pos2, team2, unit_type2, entity_type2) in esper.get_components(
        Position, Team, UnitType, EntityType
    ):

        if team2.team_id == team.team_id:
            continue
        if not (
            unit_type2 in target.allow_targets or entity_type2 in target.allow_targets
        ):
            continue

        dist_sq: float = pos.distance_to(pos2)

        if dist_sq < vision_range and dist_sq < nearest_dist_sq:
            nearest_enemy = other
            nearest_dist_sq = dist_sq

    if nearest_enemy:
        ctrl.target = nearest_enemy
        return True

    ctrl.target = None
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
    pos: Position = esper.component_for_entity(ent, Position)
    vel: Velocity = esper.component_for_entity(ent, Velocity)
    atk: Attack = esper.component_for_entity(ent, Attack)

    # If there is no target
    if not ctrl.target or not esper.entity_exists(ctrl.target):
        ctrl.target = None
        return Status.FAILURE

    target_pos: Position = esper.component_for_entity(ctrl.target, Position)
    dist: float = pos.distance_to(target_pos)

    # Attack or move to target
    if dist <= atk.range:
        vel.x = vel.y = 0
        ctrl.state = Animation.ATTACK
        return Status.RUNNING
    else:
        ctrl.state = Animation.WALK
        return move_to(ent, target_pos, force=True)


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
    pos: Position = esper.component_for_entity(ent, Position)
    ctrl: AIController = esper.component_for_entity(ent, AIController)

    if not ctrl.path:
        target = Position(
            pos.x + random.randint(-500, 500), pos.y + random.randint(-500, 500)
        )
        ctrl.target_pos = target
        return move_to(ent, target)

    if ctrl.target_pos:
        return move_to(ent, ctrl.target_pos)

    return Status.RUNNING


def move_to(ent: int, target: Position, force: bool = False) -> Status:
    """
    Moves an entity toward a target position using A* pathfinding.

    Automatically recalculates the path if:
    - No current path exists, or
    - `force` is True and the target has significantly changed.

    Args:
        ent (int): The entity ID to move.
        target (Position): The desired destination.
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

    from core.services import Services

    tile_size = Services.config.get("tile_size")

    # To get a path if there is no path or if necessary to force a new path (to force, entity must not be on his target)
    if not ctrl.path or (
        force
        and (
            ctrl.target_pos is None
            or ctrl.target_pos.distance_to(target) > tile_size * 2
        )
    ):

        path = astar(pos, target)
        if not path or len(path) < 2:
            vel.x = vel.y = 0
            ctrl.state = Animation.IDLE
            return Status.FAILURE

        ctrl.path = path[1:]
        ctrl.target_pos = ctrl.path[0]

    if ctrl.target_pos is None and ctrl.path:
        ctrl.target_pos = ctrl.path[0]

    # If entity have a position to go
    if ctrl.target_pos:
        dx = ctrl.target_pos.x - pos.x
        dy = ctrl.target_pos.y - pos.y
        dist = math.hypot(dx, dy)

        if dist < 5:
            ctrl.path.pop(0)
            if ctrl.path:
                ctrl.target_pos = ctrl.path[0]
            else:
                ctrl.target_pos = None
                vel.x = vel.y = 0
                ctrl.state = Animation.IDLE
                return Status.SUCCESS
        else:
            speed = vel.speed
            vel.x = dx / dist * speed
            vel.y = dy / dist * speed
            ctrl.state = Animation.WALK
            return Status.RUNNING

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
