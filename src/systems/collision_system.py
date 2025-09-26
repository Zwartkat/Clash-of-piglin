from components.velocity import Velocity
from config.terrain_config import (
    COLLISION_CONFIG,
    COLLISION_TYPE_RULES,
    TERRAIN_PROPERTIES,
)
from core.iterator_system import IteratingProcessor
from components.position import Position
from components.collider import Collider
import esper

TILE_SIZE = 32


class CollisionSystem(IteratingProcessor):
    def __init__(self, game_map):
        super().__init__(Position, Collider)
        self.game_map = game_map

    def process_entity(self, ent, dt, pos, collider):
        if COLLISION_CONFIG["enable_entity_collision"]:
            for ent2, (pos2, collider2) in esper.get_components(Position, Collider):
                if ent != ent2 and self.check_collision(pos, collider, pos2, collider2):
                    self.resolve_collision(pos, pos2, collider, collider2)

        if COLLISION_CONFIG["enable_terrain_collision"]:
            self.check_terrain_wall_collision(ent, pos, collider)

    def check_terrain_wall_collision(self, ent, pos, collider):
        left = pos.x - collider.width // 2
        right = pos.x + collider.width // 2
        top = pos.y - collider.height // 2
        bottom = pos.y + collider.height // 2

        tile_left = int(left // TILE_SIZE)
        tile_right = int(right // TILE_SIZE)
        tile_top = int(top // TILE_SIZE)
        tile_bottom = int(bottom // TILE_SIZE)

        for tile_y in range(tile_top, tile_bottom + 1):
            for tile_x in range(tile_left, tile_right + 1):
                if self.is_tile_blocking(tile_x, tile_y, collider.collision_type):
                    self.resolve_terrain_collision(ent, pos, collider, tile_x, tile_y)

    def is_tile_blocking(self, tile_x, tile_y, collision_type):
        if (
            tile_x < 0
            or tile_x >= len(self.game_map.tab[0])
            or tile_y < 0
            or tile_y >= len(self.game_map.tab)
        ):
            return True

        terrain_type = self.game_map.tab[tile_y][tile_x].type

        rules = COLLISION_TYPE_RULES.get(collision_type, {})
        can_cross = rules.get("can_cross", {})
        return not can_cross.get(terrain_type, True)

    def resolve_terrain_collision(self, ent, pos, collider, tile_x, tile_y):
        tile_left = tile_x * TILE_SIZE
        tile_right = (tile_x + 1) * TILE_SIZE
        tile_top = tile_y * TILE_SIZE
        tile_bottom = (tile_y + 1) * TILE_SIZE

        entity_left = pos.x - collider.width // 2
        entity_right = pos.x + collider.width // 2
        entity_top = pos.y - collider.height // 2
        entity_bottom = pos.y + collider.height // 2

        overlap_left = entity_right - tile_left
        overlap_right = tile_right - entity_left
        overlap_top = entity_bottom - tile_top
        overlap_bottom = tile_bottom - entity_top

        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

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

    def check_collision(self, pos1, col1, pos2, col2):
        dx = abs(pos2.x - pos1.x)
        dy = abs(pos2.y - pos1.y)
        half_width = (col1.width + col2.width) / 2
        half_height = (col1.height + col2.height) / 2
        return dx < half_width and dy < half_height

    def resolve_collision(self, pos1, pos2, col1, col2):
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance < 0.1:
            dx, dy = 1, 0
            distance = 1

        dx /= distance
        dy /= distance

        min_distance = (col1.width + col2.width) / 2
        push_distance = (min_distance - distance) / 2

        pos1.x += dx * push_distance
        pos1.y += dy * push_distance
        pos2.x -= dx * push_distance
        pos2.y -= dy * push_distance
