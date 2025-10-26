import esper
import heapq
import math
from typing import List, Tuple, Optional, Set

from components.position import Position
from components.ai import PathRequest
from enums.case_type import CaseType


class Node:
    """
    Represents a node in the pathfinding grid.
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


PATHFINDING_SYSTEM_INSTANCE = None


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

    def __init__(self, tile_size: int = 32):
        """
        Initialize the pathfinding system.

        Args:
            tile_size (int): Size of each grid tile in pixels. Defaults to 32.
        """
        super().__init__()
        self.tile_size = tile_size
        self.map_width = 24
        self.map_height = 24
        self.terrain_map = {}  # Terrain data storage
        self._terrain_loaded = False  # Flag to prevent reloading
        self._load_terrain_map()

        # Debug info
        self.debug_mode = False
        self.debug_lines = []  # list of ((x1, y1), (x2, y2), color)
        self.debug_texts = []  # list of (x, y, text, color)

        global PATHFINDING_SYSTEM_INSTANCE
        PATHFINDING_SYSTEM_INSTANCE = self

    def _load_terrain_map(self):
        """
        Load terrain data from the game map.

        Attempts to extract terrain information from Map components in the ECS.
        If no map is found, creates a default terrain map.
        """
        if self._terrain_loaded:
            return

        self.terrain_map = {}

        try:
            from components.map import Map
            from enums.case_type import CaseType

            map_found = False

            # Try to get all entities and check for Map components
            all_entities = (
                list(esper._entities.keys()) if hasattr(esper, "_entities") else []
            )

            # Method 1: Try the original way
            for ent, map_comp in esper.get_components(Map):
                if (
                    isinstance(map_comp, Map)
                    and hasattr(map_comp, "tab")
                    and map_comp.tab
                ):
                    map_found = True
                    self._process_map_data(map_comp)
                    break

            # Method 2: If not found, try checking all entities directly
            if not map_found:
                for entity_id in all_entities:
                    try:
                        if esper.has_component(entity_id, Map):
                            map_comp = esper.component_for_entity(entity_id, Map)
                            if (
                                isinstance(map_comp, Map)
                                and hasattr(map_comp, "tab")
                                and map_comp.tab
                            ):
                                map_found = True
                                self._process_map_data(map_comp)
                                break
                    except Exception:
                        continue

            if not map_found:
                print("[Pathfinding] NO MAP FOUND - Using default terrain map")
                self._create_default_terrain()
            else:
                print("[Pathfinding] REAL MAP LOADED successfully")

        except Exception as e:
            print(f"[Pathfinding] ERROR loading map: {e}")
            self._create_default_terrain()

        self._terrain_loaded = True

    def _process_map_data(self, map_comp):
        """
        Process the Map component data and load terrain information.

        Args:
            map_comp: Map component containing terrain data
        """
        from enums.case_type import CaseType

        for y in range(len(map_comp.tab)):
            for x in range(len(map_comp.tab[y])):
                case = map_comp.tab[y][x]
                if hasattr(case, "getType"):
                    case_type = case.getType()
                    if case_type == CaseType.LAVA:
                        self.terrain_map[(x, y)] = "LAVA"
                    elif case_type == CaseType.SOULSAND:
                        self.terrain_map[(x, y)] = "SLOW"
                    else:
                        self.terrain_map[(x, y)] = "WALKABLE"

    def _create_default_terrain(self):
        """Create a default terrain map for fallback purposes."""
        for x in range(self.map_width):
            for y in range(self.map_height):
                # Create some lava zones for testing
                if (x in [5, 6, 7] and y in [10, 11, 12]) or (
                    x in [15, 16] and y in [8, 9]
                ):
                    self.terrain_map[(x, y)] = "LAVA"
                else:
                    self.terrain_map[(x, y)] = "WALKABLE"

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
        terrain_type = self.terrain_map.get((x, y), "WALKABLE")

        # LAVA is impassable, SOULSAND is slow but walkable, everything else is walkable
        if terrain_type == "LAVA":
            return False

        return True  # SOULSAND, WALKABLE, and unknown terrains are passable

    def _get_terrain_cost(self, x: int, y: int) -> float:
        """
        Get the movement cost for a specific terrain tile.

        Args:
            x (int): Grid X coordinate
            y (int): Grid Y coordinate

        Returns:
            float: Movement cost (1.0 = normal, higher = slower)
        """
        terrain_type = self.terrain_map.get((x, y), "WALKABLE")

        if terrain_type == "LAVA":
            return float("inf")  # Impassable
        elif terrain_type == "SOULSAND":
            return 2.0  # Slow terrain - double movement cost
        else:
            # Add additional cost near lava to avoid getting too close
            lava_penalty = self._get_lava_proximity_cost(x, y)
            return 1.0 + lava_penalty  # Normal terrain + penalty if near lava

    def _get_lava_proximity_cost(self, x: int, y: int) -> float:
        """
        Calculate additional cost for being near lava tiles.

        Args:
            x (int): Grid X coordinate
            y (int): Grid Y coordinate

        Returns:
            float: Additional cost penalty for lava proximity
        """
        proximity_cost = 0.0

        # Check within a 2-tile radius around current position
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue

                check_x, check_y = x + dx, y + dy
                if 0 <= check_x < self.map_width and 0 <= check_y < self.map_height:

                    terrain = self.terrain_map.get((check_x, check_y), "WALKABLE")
                    if terrain == "LAVA":
                        distance = abs(dx) + abs(dy)  # Manhattan distance
                        if distance == 1:
                            proximity_cost += 2.0  # High penalty near lava
                        elif distance == 2:
                            proximity_cost += 0.5  # Moderate penalty

        return proximity_cost

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

    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """
        Calculate Manhattan distance between two grid positions for A* heuristic.

        Args:
            x1 (int): X coordinate of first position
            y1 (int): Y coordinate of first position
            x2 (int): X coordinate of second position
            y2 (int): Y coordinate of second position

        Returns:
            float: Manhattan distance between the two positions
        """
        return abs(x1 - x2) + abs(y1 - y2)

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
        # Inclure les diagonales pour un pathfinding plus fluide
        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),  # Cardinaux
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),  # Diagonales
        ]

        for dx, dy in directions:
            new_x = node.x + dx
            new_y = node.y + dy

            # Check if the tile is walkable
            if self._is_walkable(new_x, new_y):
                # For diagonal movements, verify adjacent tiles are also walkable
                # (prevents cutting corners through lava)
                if abs(dx) + abs(dy) == 2:  # Diagonal movement
                    if self._is_walkable(node.x + dx, node.y) and self._is_walkable(
                        node.x, node.y + dy
                    ):
                        neighbors.append(Node(new_x, new_y))
                else:  # Cardinal movement
                    neighbors.append(Node(new_x, new_y))

        return neighbors

    def find_path(
        self, start_pos: Position, end_pos: Position, entity_id: int
    ) -> Optional[List[Position]]:
        """Trouve un chemin de start_pos à end_pos en utilisant A*"""
        # Convert positions to grid coordinates
        start_x = int(start_pos.x // self.tile_size)
        start_y = int(start_pos.y // self.tile_size)
        end_x = int(end_pos.x // self.tile_size)
        end_y = int(end_pos.y // self.tile_size)

        # Limiter aux bornes de la grille
        start_x = max(0, min(start_x, self.map_width - 1))
        start_y = max(0, min(start_y, self.map_height - 1))
        end_x = max(0, min(end_x, self.map_width - 1))
        end_y = max(0, min(end_y, self.map_height - 1))

        # Temporary debug to see if function is called
        if self.debug_mode:
            print(
                f"PATHFINDING DEMANDE pour entité {entity_id} de ({start_x},{start_y}) vers ({end_x},{end_y})"
            )

        # Add debug info if debug mode is active
        if self.debug_mode:
            self._add_debug_text(
                f"Entity {entity_id}: Start({start_x},{start_y}) -> Goal({end_x},{end_y})",
                (start_pos.x, start_pos.y - 40),
                (255, 255, 0),
                180,
            )

        # Check if destination is valid
        if not self._is_walkable(end_x, end_y):
            if self.debug_mode:
                self._add_debug_text(
                    f"Goal blocked! Terrain: {self.terrain_map.get((end_x, end_y), 'UNKNOWN')}",
                    (end_pos.x, end_pos.y - 20),
                    (255, 100, 100),
                    120,
                )
            # Chercher la case valide la plus proche
            end_x, end_y = self._find_nearest_walkable(end_x, end_y)
            if end_x is None:
                if self.debug_mode:
                    self._add_debug_text(
                        "No walkable destination found!",
                        (end_pos.x, end_pos.y),
                        (255, 0, 0),
                        180,
                    )
                return None
            if self.debug_mode:
                self._add_debug_text(
                    f"New goal: ({end_x},{end_y})",
                    (end_x * self.tile_size, end_y * self.tile_size),
                    (100, 255, 100),
                    120,
                )

        # Check if start is valid
        if not self._is_walkable(start_x, start_y):
            if self.debug_mode:
                self._add_debug_text(
                    f"Start blocked! Terrain: {self.terrain_map.get((start_x, start_y), 'UNKNOWN')}",
                    (start_pos.x, start_pos.y),
                    (255, 0, 0),
                    120,
                )
            return None

        # Algorithme A*
        start_node = Node(
            start_x, start_y, 0, self._heuristic(start_x, start_y, end_x, end_y)
        )
        open_set = [start_node]
        closed_set: Set[Tuple[int, int]] = set()
        iterations = 0
        max_iterations = 1000  # Limit to prevent infinite loops

        while open_set and iterations < max_iterations:
            iterations += 1
            # Get node with lowest cost
            current = heapq.heappop(open_set)

            # Check if we reached the destination
            if current.x == end_x and current.y == end_y:
                # Reconstruire le chemin
                path = []
                while current:
                    # Convert grid coordinates to pixel positions
                    pos = Position(
                        current.x * self.tile_size + self.tile_size // 2,
                        current.y * self.tile_size + self.tile_size // 2,
                    )
                    path.append(pos)
                    current = current.parent
                path.reverse()

                # Add debug lines if debug mode is active
                if self.debug_mode:
                    self._add_debug_path(path, entity_id)
                    self._add_debug_text(
                        f"Path found! {iterations} iterations, {len(path)} steps",
                        (path[0].x + 20, path[0].y - 60),
                        (100, 255, 100),
                        180,
                    )

                return path[1:]  # Exclude starting position

            closed_set.add((current.x, current.y))

            # Explorer les voisins
            neighbors = self._get_neighbors(current, entity_id)

            for neighbor in neighbors:
                if (neighbor.x, neighbor.y) in closed_set:
                    continue

                # Calculate movement cost from current to neighbor
                terrain_cost = self._get_terrain_cost(neighbor.x, neighbor.y)
                movement_cost = 1.0  # Base movement cost

                # Add diagonal movement penalty if applicable
                if abs(neighbor.x - current.x) + abs(neighbor.y - current.y) > 1:
                    movement_cost = 1.414  # sqrt(2) for diagonal movement

                # Calculate total cost to reach this neighbor
                neighbor.g = current.g + (movement_cost * terrain_cost)
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

        # Pathfinding failed
        if self.debug_mode:
            self._add_debug_text(
                f"Pathfinding FAILED! {iterations} iterations",
                (start_pos.x, start_pos.y - 20),
                (255, 0, 0),
                240,
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

        Handles path requests and executes A* pathfinding for entities
        with PathRequest components.

        Args:
            dt: Delta time (not used in current implementation)
        """
        # Update debug texts (remove expired ones)
        if self.debug_mode:
            self._update_debug_texts()

        # Try to reload terrain map if it's still using default
        if (
            not self._terrain_loaded or len(self.terrain_map) <= 100
        ):  # Default map is small
            self._terrain_loaded = False  # Force reload
            self._load_terrain_map()

        for ent, (path_req, pos) in esper.get_components(PathRequest, Position):
            # If a new destination is requested
            if path_req.destination and not path_req.path:
                # destination is already a Position object, not a tuple
                dest_pos = path_req.destination
                new_path = self.find_path(pos, dest_pos, ent)

                if new_path:
                    path_req.path = new_path
                    path_req.current_index = 0
                else:
                    path_req.destination = None  # Reset the request

    def toggle_debug(self):
        """Active/désactive le mode debug."""
        self.debug_mode = not self.debug_mode
        if not self.debug_mode:
            self.clear_debug()

    def clear_debug(self):
        """Efface toutes les données de debug."""
        self.debug_lines.clear()
        self.debug_texts.clear()

    def _add_debug_text(self, text, position, color, timeout=120):
        """Ajoute un texte de debug à la position donnée avec un timeout en frames."""
        text_info = (text, position, color, timeout)
        self.debug_texts.append(text_info)

    def _update_debug_texts(self):
        """Met à jour les textes de debug (enlève ceux expirés)."""
        updated_texts = []
        for text_info in self.debug_texts:
            if len(text_info) >= 4:  # Avec timeout
                text, position, color, timeout = text_info
                if timeout > 0:
                    updated_texts.append((text, position, color, timeout - 1))
            else:  # Sans timeout (permanent)
                updated_texts.append(text_info)
        self.debug_texts = updated_texts

    def _add_debug_path(self, path, entity_id):
        """Ajoute un chemin aux données de debug."""
        if len(path) < 2:
            return

        # Remove old path for this entity if it exists
        self.debug_lines = [
            (lines, eid) for lines, eid in self.debug_lines if eid != entity_id
        ]

        # Convert Position objects to pixel coordinates
        pixel_path = []
        for pos in path:
            pixel_path.append((pos.x, pos.y))

        # Ajouter les lignes du chemin
        lines = []
        for i in range(len(pixel_path) - 1):
            lines.append((pixel_path[i], pixel_path[i + 1]))

        if lines:
            self.debug_lines.append((lines, entity_id))

        # Add debug text for path start
        if pixel_path:
            start_pos = pixel_path[0]
            text_info = (
                f"Path {entity_id}",
                start_pos,
                (0, 255, 0),
            )  # Vert, sans timeout (permanent)
            self.debug_texts.append(text_info)
