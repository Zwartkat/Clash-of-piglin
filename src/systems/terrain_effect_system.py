import esper
from components.case import Case
from components.fly import Fly
from components.map import Map
from components.position import Position
from components.effects import Slowed, OnTerrain
from config.terrains import TERRAIN
from core.config import Config
from core.iterator_system import IteratingProcessor
from core.terrain import Terrain
from enums.case_type import CaseType
from enums.source_effect import SourceEffect

tile_size: int = Config.TILE_SIZE()


class TerrainEffectSystem(IteratingProcessor):
    """Applies terrain effects like slow down on Soul Sand to walking units."""

    def __init__(self, game_map: Map):
        super().__init__(Position, OnTerrain)
        self.game_map: Map = game_map

    def process_entity(self, ent: int, dt: float, pos: Position, on_terrain: OnTerrain):
        """
        Check if entity changed terrain and apply new terrain effects.

        Args:
            ent: Entity ID number
            dt: Time passed since last frame
            pos: Entity position on map
            on_terrain: Entity current terrain info
        """
        # Flying units ignore all terrain effects
        if esper.has_component(ent, Fly):
            return

        current_case: Case = self.get_terrain_at_position(pos)
        if current_case != on_terrain.terrain_type:
            self._clear_terrain_effects(ent)
            try:
                self._apply_terrain_effects(ent, current_case.type)
                on_terrain.previous_terrain = on_terrain.terrain_type
                on_terrain.terrain_type = current_case.type
            except:
                # print(current_case, type(current_case), pos)
                pass

    def get_terrain_at_position(self, pos: Position) -> Case | None:
        """
        Get terrain case at world position.

        Args:
            pos: World position to check

        Returns:
            Case: Terrain case at position or None if outside map
        """
        tile_x: int = int(pos.x // tile_size)
        tile_y: int = int(pos.y // tile_size)

        if 0 <= tile_x < len(self.game_map.tab[0]) and 0 <= tile_y < len(
            self.game_map.tab
        ):
            return self.game_map.tab[tile_y][tile_x]
        return None

    def _clear_terrain_effects(self, ent: int):
        """
        Remove all terrain-based effects from entity.

        Args:
            ent: Entity ID to clear effects from
        """
        if esper.has_component(ent, Slowed):
            slowed = esper.component_for_entity(ent, Slowed)
            if slowed.source == SourceEffect.TERRAIN:
                esper.remove_component(ent, Slowed)

    def _apply_terrain_effects(self, ent: int, terrain_type: CaseType):
        """
        Apply terrain effects based on terrain type (Soul Sand slows down).

        Args:
            ent: Entity ID to apply effects to
            terrain_type: Type of terrain (Soul Sand, Lava, etc.)
        """
        if not terrain_type:
            return

        terrain: Terrain | None = TERRAIN.get(terrain_type, None)

        if not terrain:
            return

        # Apply speed reduction for slow terrains like Soul Sand
        if terrain.speed_modifier < 1.0:
            if not esper.has_component(ent, Slowed):
                esper.add_component(
                    ent,
                    Slowed(factor=terrain.speed_modifier, source=SourceEffect.TERRAIN),
                )
