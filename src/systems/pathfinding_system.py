import esper
import heapq
import math
from typing import List, Tuple, Optional, Set

from components.position import Position
from components.ai import PathRequest
from enums.case_type import CaseType


class Node:
    """
    Represents a node in the A* pathfinding algorithm.

    Attributes:
        x (int): Grid X coordinate
        y (int): Grid Y coordinate
        g (float): Distance from start node
        h (float): Heuristic distance to goal
        f (float): Total cost (g + h)
        parent (Node): Parent node in the path
    """

    def __init__(self, x: int, y: int, g: float = 0, h: float = 0, parent=None):
        """
        Initialize a new pathfinding node.

        Args:
            x (int): Grid X coordinate
            y (int): Grid Y coordinate
            g (float): Distance from start node
            h (float): Heuristic distance to goal
            parent (Node, optional): Parent node in the path
        """
        self.x = x
        self.y = y
        self.g = g  # Distance from start
        self.h = h  # Heuristic to goal
        self.f = g + h  # Total cost
        self.parent = parent

    def __lt__(self, other):
        """Compare nodes by total cost for priority queue."""
        return self.f < other.f

    def __eq__(self, other):
        """Check if two nodes are at the same position."""
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        """Hash function for set operations."""
        return hash((self.x, self.y))


class PathfindingSystem(esper.Processor):
    """
    A* pathfinding system for navigating units around terrain obstacles.

    This system handles pathfinding requests from AI entities, calculates optimal
    paths around obstacles like lava, and manages terrain data loading.

    Attributes:
        tile_size (int): Size of each grid tile in pixels
        map_width (int): Width of the game map in tiles
        map_height (int): Height of the game map in tiles
        terrain_map (dict): Dictionary mapping grid coordinates to terrain types
    """

    def __init__(self, tile_size: int = 24):
        """
        Initialize the pathfinding system.

        Args:
            tile_size (int): Size of each grid tile in pixels. Defaults to 24.
        """
        super().__init__()
        self.tile_size = tile_size
        self.map_width = 24
        self.map_height = 24
        self.terrain_map = {}  # Terrain data storage
        self._load_terrain_map()

    def _load_terrain_map(self):
        """
        Load terrain data from the game map.

        Attempts to extract terrain information from Map components in the ECS.
        If no map is found, creates a default terrain map with some lava obstacles
        for testing purposes.
        """
        # Reset the terrain map
        self.terrain_map = {}
        print("[Pathfinding] Loading terrain map...")

        # Search for Map component in ECS
        try:
            from components.map import Map

            for ent, map_comp in esper.get_components(Map):
                print(f"[Pathfinding] Map found with entity {ent}")
                # Map uses self.tab[i][j] with Case objects
                if hasattr(map_comp, "tab"):
                    print(
                        f"[Pathfinding] Map size: {len(map_comp.tab)}x{len(map_comp.tab[0]) if map_comp.tab else 0}"
                    )
                    for i in range(len(map_comp.tab)):
                        for j in range(len(map_comp.tab[i])):
                            case = map_comp.tab[i][j]
                            if hasattr(case, "getType"):
                                case_type = case.getType()
                                self.terrain_map[(i, j)] = case_type
                                if case_type == CaseType.LAVA:
                                    print(f"[Pathfinding] Lava detected at ({i}, {j})")
                    print(
                        f"[Pathfinding] Map loaded with {len(self.terrain_map)} tiles"
                    )
                break  # Take the first map found
        except Exception as e:
            print(f"[Pathfinding] Error during loading: {e}")

        # If no map found, create a default terrain map
        if not self.terrain_map:
            print("[Pathfinding] Using default terrain map")
            for x in range(self.map_width):
                for y in range(self.map_height):
                    # Create some lava zones for testing
                    if (x in [5, 6, 7] and y in [10, 11, 12]) or (
                        x in [15, 16] and y in [8, 9]
                    ):
                        self.terrain_map[(x, y)] = CaseType.LAVA
                    else:
                        self.terrain_map[(x, y)] = CaseType.NETHERRACK
        else:
            print(f"[Pathfinding] Real map loaded with {len(self.terrain_map)} tiles")

    def _is_walkable(self, x: int, y: int) -> bool:
        """
        Check if a grid tile is walkable for units.

        Args:
            x (int): Grid X coordinate
            y (int): Grid Y coordinate

        Returns:
            bool: True if the tile is walkable, False otherwise
        """
        # Check map boundaries
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return False

        # Check terrain type
        terrain_type = self.terrain_map.get((x, y), CaseType.NETHERRACK)

        # CRITICAL FIX: Consider UNKNOWN as walkable to avoid blocking
        if terrain_type is None or terrain_type == "UNKNOWN":
            return True  # Default: if terrain unknown, allow passage

        return terrain_type != CaseType.LAVA  # Only lava is impassable

    def _is_occupied_by_unit(self, x: int, y: int, current_entity: int) -> bool:
        """
        Check if a grid tile is occupied by another unit.

        Args:
            x (int): Grid X coordinate to check
            y (int): Grid Y coordinate to check
            current_entity (int): Entity ID to exclude from check

        Returns:
            bool: True if tile is occupied by another unit, False otherwise
        """
        from components.team import Team
        from enums.entity_type import EntityType

        target_x = x * self.tile_size
        target_y = y * self.tile_size

        for ent, (pos, team, entity_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ent == current_entity:
                continue

            # Check if a unit is on this tile (with tolerance)
            unit_grid_x = int(pos.x // self.tile_size)
            unit_grid_y = int(pos.y // self.tile_size)

            if unit_grid_x == x and unit_grid_y == y:
                return True

        return False

    def _heuristic(self, node1: Node, node2: Node) -> float:
        """
        Calculate Manhattan distance between two nodes for A* heuristic.

        Args:
            node1 (Node): First node
            node2 (Node): Second node

        Returns:
            float: Manhattan distance between the two nodes
        """
        return abs(node1.x - node2.x) + abs(node1.y - node2.y)

    def _get_neighbors(self, node: Node, entity_id: int) -> List[Node]:
        """
        Get valid neighboring nodes for pathfinding.

        Args:
            node (Node): Current node to find neighbors for
            entity_id (int): ID of entity for collision checking

        Returns:
            List[Node]: List of walkable neighboring nodes
        """
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Left, right, up, down

        for dx, dy in directions:
            new_x = node.x + dx
            new_y = node.y + dy

            if self._is_walkable(new_x, new_y, entity_id):
                neighbors.append(Node(new_x, new_y))

        return neighbors

    def find_path(
        self, start_pos: Position, end_pos: Position, entity_id: int
    ) -> Optional[List[Position]]:
        """Trouve un chemin de start_pos à end_pos en utilisant A*"""
        # Convertir les positions en coordonnées de grille
        start_x = int(start_pos.x // self.tile_size)
        start_y = int(start_pos.y // self.tile_size)
        end_x = int(end_pos.x // self.tile_size)
        end_y = int(end_pos.y // self.tile_size)

        print(f"[Pathfinding] A* pour entité {entity_id}:")
        print(
            f"  Position pixel: ({start_pos.x}, {start_pos.y}) -> ({end_pos.x}, {end_pos.y})"
        )
        print(f"  Position grille: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        print(f"  Taille carte: {len(self.terrain_map)} cases")

        # Vérifier si la destination est valide
        if not self._is_walkable(end_x, end_y):
            print(
                f"  Destination ({end_x}, {end_y}) non marchable: {self.terrain_map.get((end_x, end_y), 'UNKNOWN')}"
            )
            # Chercher la case valide la plus proche
            end_x, end_y = self._find_nearest_walkable(end_x, end_y)
            if end_x is None:
                print("  Aucune destination marchable trouvée")
                return None
            print(f"  Nouvelle destination: ({end_x}, {end_y})")

        # Vérifier si le début est valide
        if not self._is_walkable(start_x, start_y):
            print(
                f"  Position de départ ({start_x}, {start_y}) non marchable: {self.terrain_map.get((start_x, start_y), 'UNKNOWN')}"
            )
            return None

        # Algorithme A*
        start_node = Node(
            start_x, start_y, 0, self._heuristic(start_x, start_y, end_x, end_y)
        )
        open_set = [start_node]
        closed_set: Set[Tuple[int, int]] = set()
        iterations = 0
        max_iterations = 1000  # Limite pour éviter les boucles infinies

        print(f"  Démarrage A* avec heuristique: {start_node.h}")

        while open_set and iterations < max_iterations:
            iterations += 1
            # Prendre le nœud avec le coût le plus faible
            current = heapq.heappop(open_set)

            # Vérifier si on a atteint la destination
            if current.x == end_x and current.y == end_y:
                # Reconstruire le chemin
                path = []
                while current:
                    # Convertir les coordonnées de grille en positions pixel
                    pos = Position(
                        current.x * self.tile_size + self.tile_size // 2,
                        current.y * self.tile_size + self.tile_size // 2,
                    )
                    path.append(pos)
                    current = current.parent
                path.reverse()
                print(
                    f"  Chemin trouvé en {iterations} itérations, longueur: {len(path)} étapes"
                )
                return path[1:]  # Exclure la position de départ

            closed_set.add((current.x, current.y))

            # Explorer les voisins
            neighbors = self._get_neighbors(current, entity_id)
            if iterations < 5:  # Debug pour les premières itérations
                print(
                    f"  Itération {iterations}: nœud ({current.x}, {current.y}), {len(neighbors)} voisins"
                )

            for neighbor in neighbors:
                if (neighbor.x, neighbor.y) in closed_set:
                    continue

                neighbor.h = self._heuristic(neighbor.x, neighbor.y, end_x, end_y)
                neighbor.f = neighbor.g + neighbor.h
                neighbor.parent = current

                # Check if this neighbor is already in open_set with a better cost
                existing = None
                for node in open_set:
                    if node.x == neighbor.x and node.y == neighbor.y:
                        existing = node
                        break

                if existing is None or neighbor.g < existing.g:
                    if existing:
                        open_set.remove(existing)
                    heapq.heappush(open_set, neighbor)

        print(
            f"  A* failed after {iterations} iterations, open_set: {len(open_set)}, closed_set: {len(closed_set)}"
        )
        return None  # No path found

    def _find_nearest_walkable(
        self, x: int, y: int, max_radius: int = 5
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Find the nearest walkable tile within a given radius.

        Args:
            x (int): Starting X grid coordinate
            y (int): Starting Y grid coordinate
            max_radius (int): Maximum search radius

        Returns:
            Tuple[Optional[int], Optional[int]]: (x, y) coordinates of nearest walkable tile, or (None, None) if none found
        """
        for radius in range(1, max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    new_x, new_y = x + dx, y + dy
                    if self._is_walkable(new_x, new_y):
                        return new_x, new_y
        return None, None

    def process(self, dt):
        """
        Process pathfinding requests from entities.

        Handles path requests, reloads terrain map periodically,
        and executes A* pathfinding for entities with PathRequest components.

        Args:
            dt: Delta time (not used in current implementation)
        """
        # Reload map if necessary (every 60 frames ~ 1 second)
        if not hasattr(self, "_map_reload_counter"):
            self._map_reload_counter = 0

        self._map_reload_counter += 1
        if self._map_reload_counter >= 60:
            self._load_terrain_map()
            self._map_reload_counter = 0

        for ent, (path_req, pos) in esper.get_components(PathRequest, Position):
            # If a new destination is requested
            if path_req.destination and not path_req.path:
                dest_pos = Position(path_req.destination[0], path_req.destination[1])
                new_path = self.find_path(pos, dest_pos, ent)

                if new_path:
                    path_req.path = new_path
                    path_req.current_index = 0
                    print(
                        f"[Pathfinding] Chemin trouvé pour entité {ent}: {len(new_path)} étapes"
                    )
                else:
                    print(f"[Pathfinding] Aucun chemin trouvé pour entité {ent}")
                    path_req.destination = None  # Reset the request
