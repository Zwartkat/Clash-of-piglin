import heapq
import itertools
import math

from components.base.position import Position
from components.case import Case
from enums.case_type import CaseType


def get_neighbors(
    node: Position, tile_size: int, map: list[list[Case]]
) -> list[Position]:
    x: int = node.x
    y: int = node.y

    map_size = len(map)

    neighbors: list[Position] = []

    for dx, dy in [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (1, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
    ]:
        nx, ny = round(x // tile_size + dx), round(y // tile_size + dy)
        if 0 <= nx < map_size and 0 <= ny < map_size:
            case: Case = map[ny][nx]
            if case.type not in [CaseType.LAVA]:
                neighbors.append(
                    Position(
                        nx * tile_size + tile_size // 2, ny * tile_size + tile_size // 2
                    )
                )

    return neighbors


def terrain_cost(case: Case) -> int:
    if case.type == CaseType.SOULSAND:
        return 2.0
    else:
        return 1.0


def heuristic(a: Position, b: Position) -> float:
    """
    Get euclidian heuristic of 2 positions

    Args:
        a (Position): First position
        b (Position): Second position

    Returns:
        float : Heuristic of provided positions
    """

    from core.services import Services

    tile_size = Services.config.get("tile_size")
    return math.hypot(
        b.x // tile_size - a.x // tile_size, b.y // tile_size - a.y // tile_size
    )


def astar(start: Position, goal: Position) -> list[Position]:
    """
    astar pathfinding, it will found the smallest way to a position

    Args:
        start (Position): Current position
        goal (Position): Destination position

    Returns:
        list[Position]: A list who correspond to the way to go to the destination
    """
    open_set = []

    from core.services import Services

    tile_size = Services.config.get("tile_size")

    counter = itertools.count()
    heapq.heappush(open_set, (0, next(counter), start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        current: Position
        _, _, current = heapq.heappop(open_set)

        if (
            (current.x // tile_size == goal.x // tile_size)
            and (goal.y // tile_size == current.y // tile_size)
        ) or f_score[current] >= 10:
            path: list[Position] = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        for neighbor in get_neighbors(current, tile_size, Services.map):
            tentative_g = g_score[current] + terrain_cost(
                Services.map[neighbor.y // tile_size][neighbor.x // tile_size]
            )
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], next(counter), neighbor))

    return None
