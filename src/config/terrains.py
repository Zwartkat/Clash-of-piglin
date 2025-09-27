from core.terrain import Terrain

from enums.unit_type import UnitType
from enums.case_type import *

TERRAIN = {
    CaseType.NETHERRACK: Terrain(
        [UnitType.WALK, UnitType.FLY], "Terrain standard du Nether"
    ),
    CaseType.BLUE_NETHERRACK: Terrain(
        [UnitType.WALK, UnitType.FLY], "Terrain standard du Nether"
    ),
    CaseType.RED_NETHERRACK: Terrain(
        [UnitType.WALK, UnitType.FLY], "Terrain standard du Nether"
    ),
    CaseType.LAVA: Terrain(
        [UnitType.FLY], "Lave ne pouvant être franchit par des unités terrestres"
    ),
    CaseType.SOULSAND: Terrain(
        [UnitType.WALK, UnitType.FLY],
        "Sables des âmes, ralentit les unités terrestres",
        0.1,
        [UnitType.WALK],
    ),
}


COLLISION_CONFIG = {
    "enable_terrain_collision": True,
    "enable_map_borders": True,
    "enable_entity_collision": True,
    "map_border_buffer": 16,
}
