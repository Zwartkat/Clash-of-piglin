import esper
from components.position import Position
from components.effects import Slowed, OnTerrain
from components.collider import Collider
from components.stats import UnitType
from core.iterator_system import IteratingProcessor
from config.terrain_config import TERRAIN_PROPERTIES

TILE_SIZE = 32


class TerrainEffectSystem(IteratingProcessor):
    def __init__(self, game_map):
        super().__init__(Position, OnTerrain)
        self.game_map = game_map

    def process_entity(self, ent, dt, pos, on_terrain):
        if esper.has_component(ent, Collider):
            collider = esper.component_for_entity(ent, Collider)
            if collider.collision_type == "flying":
                return

        current_terrain = self.get_terrain_at_position(pos)

        if current_terrain != on_terrain.terrain_type:
            self._clear_terrain_effects(ent)
            self._apply_terrain_effects(ent, current_terrain)

            on_terrain.previous_terrain = on_terrain.terrain_type
            on_terrain.terrain_type = current_terrain

    def get_terrain_at_position(self, pos):
        tile_x = int(pos.x // TILE_SIZE)
        tile_y = int(pos.y // TILE_SIZE)

        if 0 <= tile_x < len(self.game_map.tab[0]) and 0 <= tile_y < len(
            self.game_map.tab
        ):
            return self.game_map.tab[tile_y][tile_x]
        return None

    def _clear_terrain_effects(self, ent):
        if esper.has_component(ent, Slowed):
            slowed = esper.component_for_entity(ent, Slowed)
            if slowed.source == "terrain":
                esper.remove_component(ent, Slowed)

    def _apply_terrain_effects(self, ent, terrain_type):
        if not terrain_type:
            return

        terrain_props = TERRAIN_PROPERTIES.get(terrain_type, {})

        speed_mod = terrain_props.get("movement_speed_modifier", 1.0)
        if speed_mod < 1.0:
            if not esper.has_component(ent, Slowed):
                esper.add_component(ent, Slowed(factor=speed_mod, source="terrain"))
