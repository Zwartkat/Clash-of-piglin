import esper
from components.case import Case
from components.fly import Fly
from components.map import Map
from components.position import Position
from components.effects import Slowed, OnTerrain
from components.collider import Collider
from components.team import Team
from components.unit import Unit
from config.terrains import TERRAIN
from core.config import Config
from core.iterator_system import IteratingProcessor
from core.terrain import Terrain
from enums.case_type import CaseType
from enums.entity_type import EntityType
from enums.source_effect import SourceEffect
from enums.unit_type import UnitType


tile_size: int = Config.TILE_SIZE()


class TerrainEffectSystem(IteratingProcessor):
    def __init__(self, game_map: Map):
        super().__init__(Position, OnTerrain)
        self.game_map: Map = game_map

    def process_entity(self, ent: int, dt: float, pos: Position, on_terrain: OnTerrain):
        if esper.has_component(ent, Fly):
            return

        current_case: Case = self.get_terrain_at_position(pos)
        if current_case != on_terrain.terrain_type:
            self._clear_terrain_effects(ent)
            self._apply_terrain_effects(ent, current_case.type)

            on_terrain.previous_terrain = on_terrain.terrain_type
            on_terrain.terrain_type = current_case.type

    def get_terrain_at_position(self, pos: Position) -> CaseType | None:
        tile_x: int = int(pos.x // tile_size)
        tile_y: int = int(pos.y // tile_size)

        if 0 <= tile_x < len(self.game_map.tab[0]) and 0 <= tile_y < len(
            self.game_map.tab
        ):

            return self.game_map.tab[tile_y][tile_x]
        return None

    def _clear_terrain_effects(self, ent: int):
        if esper.has_component(ent, Slowed):
            slowed = esper.component_for_entity(ent, Slowed)
            if slowed.source == SourceEffect.TERRAIN:
                esper.remove_component(ent, Slowed)

    def _apply_terrain_effects(self, ent: int, terrain_type: CaseType):
        if not terrain_type:
            return

        terrain: Terrain | None = TERRAIN.get(terrain_type, None)

        if not terrain:
            return

        if terrain.speed_modifier < 1.0:
            if not esper.has_component(ent, Slowed):
                esper.add_component(
                    ent,
                    Slowed(factor=terrain.speed_modifier, source=SourceEffect.TERRAIN),
                )
