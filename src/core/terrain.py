from dataclasses import dataclass, field
from enums.unit_type import UnitType


@dataclass(frozen=False)
class Terrain:
    walkable: list[UnitType]
    description: str
    speed_modifier: float = 1.0
    affected: list[UnitType] = field(default_factory=list)
