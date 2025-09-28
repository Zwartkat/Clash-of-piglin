from typing import Tuple

import esper

from components.fly import Fly
from core.iterator_system import IteratingProcessor
from core.config import Config

from config.terrains import TERRAIN, COLLISION_CONFIG

from components.map import Map
from components.case import Case
from components.velocity import Velocity
from components.position import Position
from components.collider import Collider
from components.unit import Unit

from core.terrain import Terrain
from enums.case_type import CaseType
from enums.entity_type import EntityType

tile_size: int = Config.TILE_SIZE()


class CollisionSystem(IteratingProcessor):
    def __init__(self, game_map: Map):
        super().__init__(Position, Collider)
        self.game_map: Map = game_map

    def process_entity(self, ent: int, dt: float, pos: Position, collider: Collider):
        # To change
        entity_layer = self._get_collision_layer(ent)

        if COLLISION_CONFIG["enable_entity_collision"]:
            for ent2, (pos2, collider2) in esper.get_components(Position, Collider):
                if ent != ent2:
                    other_layer = self._get_collision_layer(ent2)

                    if self._should_collide(entity_layer, other_layer):
                        if self.check_collision(pos, collider, pos2, collider2):
                            self.resolve_collision(pos, pos2, collider, collider2)

        # To change
        if COLLISION_CONFIG["enable_terrain_collision"]:
            self.check_terrain_wall_collision(ent, pos, collider)

    def _get_collision_layer(self, ent: int) -> str:
        if esper.has_component(ent, Fly):
            return "flying"

        if esper.has_component(ent, Unit):
            unit = esper.component_for_entity(ent, Unit)
            if unit.entity_type == EntityType.GHAST:
                return "flying"

        return "ground"

    def _should_collide(self, layer1: str, layer2: str) -> bool:
        collision_matrix = {
            ("ground", "ground"): True,  # Ground block each other
            ("ground", "flying"): False,  # Ground does not block flying
            ("flying", "ground"): False,  # Flying does not block ground
            ("flying", "flying"): True,  # Ghasts block each other
        }
        return collision_matrix.get((layer1, layer2), False)

    def check_terrain_wall_collision(self, ent: int, pos: Position, collider: Collider):
        left: int = pos.x - collider.width // 2
        right: int = pos.x + collider.width // 2
        top: int = pos.y - collider.height // 2
        bottom: int = pos.y + collider.height // 2

        tile_left: int = int(left // tile_size)
        tile_right: int = int(right // tile_size)
        tile_top: int = int(top // tile_size)
        tile_bottom: int = int(bottom // tile_size)

        if not esper.has_component(ent, Unit):
            return

        unit: Unit = esper.component_for_entity(ent, Unit)

        for tile_y in range(tile_top, tile_bottom + 1):
            for tile_x in range(tile_left, tile_right + 1):
                if self.is_tile_blocking(unit, tile_x, tile_y):
                    self.resolve_terrain_collision(ent, pos, collider, tile_x, tile_y)

    def is_tile_blocking(self, unit: Unit, tile_x: int, tile_y: int):
        if (
            tile_x < 0
            or tile_x >= len(self.game_map.tab[0])
            or tile_y < 0
            or tile_y >= len(self.game_map.tab)
        ):
            return True

        case: Case = self.game_map.tab[tile_y][tile_x]

        terrain: Terrain = TERRAIN.get(case.type)

        return unit.unit_type not in terrain.walkable

    def resolve_terrain_collision(
        self, ent: int, pos: Position, collider: Collider, tile_x: int, tile_y: int
    ):
        tile_left: int = tile_x * tile_size
        tile_right: int = (tile_x + 1) * tile_size
        tile_top: int = tile_y * tile_size
        tile_bottom: int = (tile_y + 1) * tile_size

        entity_left: int = pos.x - collider.width // 2
        entity_right: int = pos.x + collider.width // 2
        entity_top: int = pos.y - collider.height // 2
        entity_bottom: int = pos.y + collider.height // 2

        overlap_left: int = entity_right - tile_left
        overlap_right: int = tile_right - entity_left
        overlap_top: int = entity_bottom - tile_top
        overlap_bottom: int = tile_bottom - entity_top

        min_overlap: int = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        if min_overlap == overlap_left:
            pos.x = tile_left - collider.width // 2 - 1
        elif min_overlap == overlap_right:
            pos.x = tile_right + collider.width // 2 + 1
        elif min_overlap == overlap_top:
            pos.y = tile_top - collider.height // 2 - 1
        elif min_overlap == overlap_bottom:
            pos.y = tile_bottom + collider.height // 2 + 1

        vel = esper.component_for_entity(ent, Velocity)
        if vel:
            if min_overlap in [overlap_left, overlap_right]:
                vel.x = 0
            if min_overlap in [overlap_top, overlap_bottom]:
                vel.y = 0

    def check_collision(self, pos1: int, col1: int, pos2: int, col2: int):
        dx: int = abs(pos2.x - pos1.x)
        dy: int = abs(pos2.y - pos1.y)
        half_width: int = (col1.width + col2.width) / 2
        half_height: int = (col1.height + col2.height) / 2
        return dx < half_width and dy < half_height

    def resolve_collision(self, pos1: int, pos2: int, col1: int, col2: int):
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance < 0.1:
            dx, dy = 1, 0
            distance = 1.0
        else:
            dx /= distance
            dy /= distance

        min_distance = (col1.width + col2.width) / 2
        overlap = min_distance - distance

        if overlap > 0:
            damping = 0.6
            separation = (overlap + 3) * damping

            pos1.x += dx * separation * 0.6
            pos1.y += dy * separation * 0.6
            pos2.x -= dx * separation * 0.4
            pos2.y -= dy * separation * 0.4
