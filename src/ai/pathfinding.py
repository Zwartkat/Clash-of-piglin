import heapq
import itertools
import math

from components.base.position import Position
from components.case import Case
from core.accessors import get_config
from core.game.map import Map
from enums.case_type import CaseType


def get_neighbors(
    node: tuple[int, int], tile_size: int, map: list[list[Case]]
) -> list[tuple[int, int]]:
    x: int = node[0] // tile_size
    y: int = node[1] // tile_size

    map_size = len(map)

    neighbors: list[Position] = []

    # Replace by a stuck system
    # def near_obstacle(px: int, py: int) -> bool:
    #    """
    #    Check if provided position is an obstacle
    #
    #    Return:
    #        bool : True if position is an obstacle else False
    #    """
    #    if not obstacles:
    #        return False
    #    for obs in obstacles:
    #        if math.hypot(obs.x - px, obs.y - py) < tile_size:
    #            return True
    #    return False

    orthogonal_directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    # Check orthogonal neighbors
    for dx, dy in orthogonal_directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < map_size and 0 <= ny < map_size:
            case: Case = map[ny][nx]
            if case.type not in [CaseType.LAVA]:
                neighbors.append(
                    (nx * tile_size + tile_size // 2, ny * tile_size + tile_size // 2)
                )

    # Check diagonal neighbors (check for corner cutting)
    for dx, dy in diagonal_directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < map_size and 0 <= ny < map_size:
            adj1 = (x + dx, y)
            adj2 = (x, y + dy)
            blocked = False
            for ax, ay in [adj1, adj2]:
                if not (0 <= ax < map_size and 0 <= ay < map_size):
                    blocked = True
                    break
                if map[ay][ax].type == CaseType.LAVA:
                    blocked = True
                    break

            if not blocked and map[ny][nx].type != CaseType.LAVA:
                neighbors.append(
                    (nx * tile_size + tile_size // 2, ny * tile_size + tile_size // 2)
                )

    return neighbors


def terrain_cost(case: Case) -> int:
    """
    Get the cost of a terrain. It will be used in pathfinding to prefer some terrain over others

    Args:
        case (Case): Case to evaluate

    Returns:
        int: Cost of the case
    """
    if case.type == CaseType.SOULSAND:
        return 2.0
    else:
        return 1.0


def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    """
    Get euclidian heuristic of 2 positions

    Args:
        a (tuple[int,int]): First position
        b (tuple[int,int]): Second position

    Returns:
        float : Heuristic of provided positions
    """

    tile_size = get_config().get("tile_size")
    return math.hypot(
        b[0] // tile_size - a[0] // tile_size, b[1] // tile_size - a[1] // tile_size
    )


def astar(
    start: Position, goal: Position, map: list[list[Case]]
) -> list[tuple[int, int]]:
    """
    astar pathfinding, it will found the smallest way to a position

    Args:
        start (Position): Current position
        goal (Position): Destination position
        map (list[list[Case]]): The map used for pathfinding

    Returns:
        list[tuple[int,int]]: A list who correspond to the way to go to the destination
    """
    open_set = []

    tile_size = get_config().get("tile_size")

    start_tuple = Position.to_tuple(start) if isinstance(start, Position) else start
    goal_tuple = Position.to_tuple(goal) if isinstance(goal, Position) else goal

    counter = itertools.count()
    heapq.heappush(open_set, (0, next(counter), start_tuple))
    came_from = {}

    # Initialize path scores (g_score for cost from start, f_score for estimated cost to goal)
    g_score: dict[tuple[int, int], float] = {start_tuple: 0}
    f_score: dict[tuple[int, int], float] = {
        start_tuple: heuristic(start_tuple, goal_tuple)
    }

    while open_set:
        current: tuple[int, int]
        # Get the position with the lowest f_score
        _, _, current = heapq.heappop(open_set)

        # Check if reached the goal or path too long (more than 24 tiles) then reconstruct path
        if (
            (current[0] // tile_size == goal_tuple[0] // tile_size)
            and (goal_tuple[1] // tile_size == current[1] // tile_size)
        ) or f_score[current] >= 32:
            path: list[tuple[int, int]] = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start_tuple)
            path.reverse()
            return path

        # Check cost for each neighbor and add them if there is a well path
        for neighbor in get_neighbors(current, tile_size, map):
            tentative_g = g_score[current] + terrain_cost(
                map[neighbor[1] // tile_size][neighbor[0] // tile_size]
            )
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal_tuple)
                # Add neighbor who is a possible positions to explore (counter is to avoid comparison issues in heap if there is two same f_score)
                heapq.heappush(open_set, (f_score[neighbor], next(counter), neighbor))

    return None
