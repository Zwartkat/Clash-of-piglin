from typing import Tuple

import esper

from components.gameplay.fly import Fly
from core.accessors import get_debugger
from core.ecs.iterator_system import IteratingProcessor
from core.config import Config

from config.terrains import TERRAIN, COLLISION_CONFIG

from core.game.map import Map
from components.case import Case
from components.base.velocity import Velocity
from components.base.position import Position
from components.gameplay.collider import Collider

from core.game.terrain import Terrain
from enums.case_type import CaseType
from enums.entity.entity_type import EntityType
from enums.entity.unit_type import UnitType

tile_size: int = Config.TILE_SIZE()


class CollisionSystem(IteratingProcessor):
    """Handles collision detection and resolution between entities and terrain."""

    def __init__(self, game_map: Map):
        super().__init__(Position, Collider)
        self.game_map: Map = game_map

    def process_entity(self, ent: int, dt: float, pos: Position, collider: Collider):
        """
        Process collision for a single entity against all others and terrain.

        Args:
            ent: Entity ID number
            dt: Time passed since last frame
            pos: Entity position on map
            collider: Entity collision box size
        """
        entity_layer = self._get_collision_layer(ent)

        # Entity vs Entity collision
        if COLLISION_CONFIG["enable_entity_collision"]:
            for ent2, (pos2, collider2) in esper.get_components(Position, Collider):
                if ent != ent2:
                    other_layer = self._get_collision_layer(ent2)

                    if self._should_collide(entity_layer, other_layer):
                        if self.check_collision(pos, collider, pos2, collider2):
                            self.resolve_collision(pos, pos2, collider, collider2)

        # Entity vs Terrain collision (only for ground entities)
        if COLLISION_CONFIG["enable_terrain_collision"]:
            self.check_terrain_wall_collision(ent, pos, collider)

    def _get_collision_layer(self, ent: int) -> str:
        """
        Get collision layer type for entity.

        Args:
            ent: Entity ID number

        Returns:
            str: "flying" for ghasts and flying units, "ground" for others
        """
        if esper.has_component(ent, Fly):
            return UnitType.FLY

        if esper.has_component(ent, UnitType):
            unit_type = esper.component_for_entity(ent, UnitType)
            return unit_type

        return UnitType.WALK

    def _should_collide(self, layer1: str, layer2: str) -> bool:
        """
        Check if two collision layers should block each other.

        Args:
            layer1: First entity collision layer
            layer2: Second entity collision layer

        Returns:
            bool: True if entities should block each other
        """
        collision_matrix = {
            (UnitType.WALK, UnitType.WALK): True,  # Ground block each other
            (UnitType.WALK, UnitType.FLY): False,  # Ground does not block flying
            (UnitType.FLY, UnitType.WALK): False,  # Flying does not block ground
            (UnitType.FLY, UnitType.FLY): True,  # Ghasts block each other
        }
        return collision_matrix.get((layer1, layer2), False)

    def check_terrain_wall_collision(self, ent: int, pos: Position, collider: Collider):
        """
        Check if entity hits walls or blocking terrain.

        Args:
            ent: Entity ID number
            pos: Entity position on map
            collider: Entity collision box size
        """
        # Calculate entity bounds
        left: int = pos.x - collider.width // 2
        right: int = pos.x + collider.width // 2
        top: int = pos.y - collider.height // 2
        bottom: int = pos.y + collider.height // 2

        # Convert to tile coordinates
        tile_left: int = int(left // tile_size)
        tile_right: int = int(right // tile_size)
        tile_top: int = int(top // tile_size)
        tile_bottom: int = int(bottom // tile_size)

        if not esper.has_component(ent, UnitType):
            return

        unit: UnitType = esper.component_for_entity(ent, UnitType)

        # Check each tile the entity overlaps
        for tile_y in range(tile_top, tile_bottom + 1):
            for tile_x in range(tile_left, tile_right + 1):
                if self.is_tile_blocking(unit, tile_x, tile_y):
                    self.resolve_terrain_collision(ent, pos, collider, tile_x, tile_y)

    def is_tile_blocking(self, unit: UnitType.WALK, tile_x: int, tile_y: int):
        """
        Check if a map tile blocks the unit from walking.

        Args:
            unit: Unit data with type info
            tile_x: Map tile X position
            tile_y: Map tile Y position

        Returns:
            bool: True if tile blocks this unit type
        """
        # Map boundaries are always blocking
        if (
            tile_x < 0
            or tile_x >= len(self.game_map.tab[0])
            or tile_y < 0
            or tile_y >= len(self.game_map.tab)
        ):
            return True

        case: Case = self.game_map.tab[tile_y][tile_x]
        terrain: Terrain = TERRAIN.get(case.type)

        return unit not in terrain.walkable

    def resolve_terrain_collision(
        self, ent: int, pos: Position, collider: Collider, tile_x: int, tile_y: int
    ):
        """
        Push entity out of blocking terrain tile.

        Args:
            ent: Entity ID number
            pos: Entity position to fix
            collider: Entity collision box size
            tile_x: Blocking tile X position
            tile_y: Blocking tile Y position
        """
        # Calculate tile bounds
        tile_left: int = tile_x * tile_size
        tile_right: int = (tile_x + 1) * tile_size
        tile_top: int = tile_y * tile_size
        tile_bottom: int = (tile_y + 1) * tile_size

        # Calculate entity bounds
        entity_left: int = pos.x - collider.width // 2
        entity_right: int = pos.x + collider.width // 2
        entity_top: int = pos.y - collider.height // 2
        entity_bottom: int = pos.y + collider.height // 2

        # Calculate overlaps from each direction
        overlap_left: int = entity_right - tile_left
        overlap_right: int = tile_right - entity_left
        overlap_top: int = entity_bottom - tile_top
        overlap_bottom: int = tile_bottom - entity_top

        # Push entity out in direction of smallest overlap
        min_overlap: int = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

        if min_overlap == overlap_left:
            pos.x = tile_left - collider.width // 2 - 1
        elif min_overlap == overlap_right:
            pos.x = tile_right + collider.width // 2 + 1
        elif min_overlap == overlap_top:
            pos.y = tile_top - collider.height // 2 - 1
        elif min_overlap == overlap_bottom:
            pos.y = tile_bottom + collider.height // 2 + 1

        # Stop velocity in collision direction
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
            if min_overlap in [overlap_left, overlap_right]:
                vel.x = 0
            if min_overlap in [overlap_top, overlap_bottom]:
                vel.y = 0

    def check_collision(self, pos1: int, col1: int, pos2: int, col2: int):
        """
        Check if two entities are touching each other.

        Args:
            pos1: First entity position
            col1: First entity collision box
            pos2: Second entity position
            col2: Second entity collision box

        Returns:
            bool: True if entities are overlapping
        """
        dx: int = abs(pos2.x - pos1.x)
        dy: int = abs(pos2.y - pos1.y)
        half_width: int = (col1.width + col2.width) / 2
        half_height: int = (col1.height + col2.height) / 2
        return dx < half_width and dy < half_height

    def resolve_collision(self, pos1: int, pos2: int, col1: int, col2: int):
        """
        Push two overlapping entities apart from each other.

        Args:
            pos1: First entity position to move
            pos2: Second entity position to move
            col1: First entity collision box
            col2: Second entity collision box
        """
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        distance = (dx**2 + dy**2) ** 0.5

        # Handle entities at exact same position
        if distance < 0.1:
            dx, dy = 1, 0
            distance = 1.0
        else:
            dx /= distance
            dy /= distance

        min_distance = (col1.width + col2.width) / 2
        overlap = min_distance - distance

        if overlap > 0:
            # Apply damping to prevent entities from sticking together
            damping = 0.6
            separation = (overlap + 3) * damping

            # Asymmetric separation to reduce mutual pulling effect
            pos1.x += dx * separation * 0.6
            pos1.y += dy * separation * 0.6
            pos2.x -= dx * separation * 0.4
            pos2.y -= dy * separation * 0.4
