from enums.case_type import CaseType
from enums.source_effect import SourceEffect


class Slowed:
    def __init__(
        self,
        factor: float = 0.5,
        source: SourceEffect = SourceEffect.TERRAIN,
        duration: int | None = None,
    ):
        self.factor: float = factor  # (0 < factor <= 1)
        self.source: SourceEffect = source
        self.duration: int | None = duration  # none infinite duration
        self.timer: float = 0.0


class Blocked:
    def __init__(self, source: SourceEffect = SourceEffect.TERRAIN):
        self.source: SourceEffect = source


class OnTerrain:
    def __init__(self, terrain_type: CaseType = CaseType.NETHERRACK):
        self.terrain_type: CaseType = terrain_type
        self.previous_terrain: CaseType = None
