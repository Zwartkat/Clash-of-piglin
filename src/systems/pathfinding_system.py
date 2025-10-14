import esper
import heapq
import math
from typing import List, Tuple, Optional, Set

from components.position import Position
from components.ai import PathRequest
from enums.case_type import CaseType


class Node:
    def __init__(self, x: int, y: int, g: float = 0, h: float = 0, parent=None):
        self.x = x
        self.y = y
        self.g = g  # Distance depuis le départ
        self.h = h  # Heuristique vers l'arrivée
        self.f = g + h  # Coût total
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class PathfindingSystem(esper.Processor):
    def __init__(self, tile_size=24):
        super().__init__()
        self.tile_size = tile_size
        self.map_width = 24
        self.map_height = 24
        self.terrain_map = {}  # Stockage du terrain
        self._load_terrain_map()

    def _load_terrain_map(self):
        """Charge la carte du terrain depuis la Map existante"""
        # Réinitialiser la carte
        self.terrain_map = {}
        print("[Pathfinding] Chargement de la carte du terrain...")

        # Chercher la Map dans les composants
        try:
            from components.map import Map

            for ent, map_comp in esper.get_components(Map):
                print(f"[Pathfinding] Map trouvée avec entité {ent}")
                # La Map utilise self.tab[i][j] avec des objets Case
                if hasattr(map_comp, "tab"):
                    print(
                        f"[Pathfinding] Taille de la carte: {len(map_comp.tab)}x{len(map_comp.tab[0]) if map_comp.tab else 0}"
                    )
                    for i in range(len(map_comp.tab)):
                        for j in range(len(map_comp.tab[i])):
                            case = map_comp.tab[i][j]
                            if hasattr(case, "getType"):
                                case_type = case.getType()
                                self.terrain_map[(i, j)] = case_type
                                if case_type == CaseType.LAVA:
                                    print(f"[Pathfinding] Lave détectée à ({i}, {j})")
                    print(
                        f"[Pathfinding] Carte chargée avec {len(self.terrain_map)} cases"
                    )
                break  # Prendre la première carte trouvée
        except Exception as e:
            print(f"[Pathfinding] Erreur lors du chargement: {e}")

        # Si aucune carte trouvée, créer une carte par défaut
        if not self.terrain_map:
            print("[Pathfinding] Utilisation de la carte par défaut")
            for x in range(self.map_width):
                for y in range(self.map_height):
                    # Créer quelques zones de lave pour tester
                    if (x in [5, 6, 7] and y in [10, 11, 12]) or (
                        x in [15, 16] and y in [8, 9]
                    ):
                        self.terrain_map[(x, y)] = CaseType.LAVA
                    else:
                        self.terrain_map[(x, y)] = CaseType.NETHERRACK
        else:
            print(
                f"[Pathfinding] Carte réelle chargée avec {len(self.terrain_map)} cases"
            )

    def _is_walkable(self, x: int, y: int) -> bool:
        """Vérifie si une case est franchissable"""
        # Vérifier les limites de la carte
        if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
            return False

        # Vérifier le type de terrain
        terrain_type = self.terrain_map.get((x, y), CaseType.NETHERRACK)

        # CORRECTION CRITIQUE: Considérer UNKNOWN comme marchable pour éviter le blocage
        if terrain_type is None or terrain_type == "UNKNOWN":
            return True  # Par défaut, si on ne connaît pas le terrain, on peut passer

        return (
            terrain_type != CaseType.LAVA
        )  # Seule la lave est infranchissable    def _is_occupied_by_unit(self, x: int, y: int, current_entity: int) -> bool:
        """Vérifie si une case est occupée par une autre unité"""
        from components.team import Team
        from enums.entity_type import EntityType

        target_x = x * self.tile_size
        target_y = y * self.tile_size

        for ent, (pos, team, entity_type) in esper.get_components(
            Position, Team, EntityType
        ):
            if ent == current_entity:
                continue

            # Vérifier si une unité est sur cette case (avec une tolérance)
            unit_grid_x = int(pos.x // self.tile_size)
            unit_grid_y = int(pos.y // self.tile_size)

            if unit_grid_x == x and unit_grid_y == y:
                return True

        return False

    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Distance euclidienne comme heuristique"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def _get_neighbors(self, node: Node, current_entity: int) -> List[Node]:
        """Retourne les voisins valides d'un nœud"""
        neighbors = []

        # 8 directions (incluant diagonales)
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for dx, dy in directions:
            new_x = node.x + dx
            new_y = node.y + dy

            # Vérifier si la case est franchissable
            if self._is_walkable(new_x, new_y):
                # Ne pas considérer les cases occupées par des unités statiques
                if not self._is_occupied_by_unit(new_x, new_y, current_entity):
                    # Coût de déplacement (diagonale coûte plus cher)
                    cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                    neighbors.append(Node(new_x, new_y, node.g + cost, 0))

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

                # Vérifier si ce voisin est déjà dans open_set avec un meilleur coût
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
            f"  A* échoué après {iterations} itérations, open_set: {len(open_set)}, closed_set: {len(closed_set)}"
        )
        return None  # Aucun chemin trouvé

    def _find_nearest_walkable(
        self, x: int, y: int, max_radius: int = 5
    ) -> Tuple[Optional[int], Optional[int]]:
        """Trouve la case franchissable la plus proche"""
        for radius in range(1, max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    new_x, new_y = x + dx, y + dy
                    if self._is_walkable(new_x, new_y):
                        return new_x, new_y
        return None, None

    def process(self, dt):
        """Traite les demandes de pathfinding"""
        # Recharger la carte si nécessaire (tous les 60 frames ~ 1 seconde)
        if not hasattr(self, "_map_reload_counter"):
            self._map_reload_counter = 0

        self._map_reload_counter += 1
        if self._map_reload_counter >= 60:
            self._load_terrain_map()
            self._map_reload_counter = 0

        for ent, (path_req, pos) in esper.get_components(PathRequest, Position):
            # Si une nouvelle destination est demandée
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
                    path_req.destination = None  # Réinitialiser la demande
