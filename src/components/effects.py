class Slowed:
    def __init__(self, factor=0.5, source="terrain", duration=None):
        self.factor = factor  # (0 < factor <= 1)
        self.source = source
        self.duration = duration  # none infinite duration
        self.timer = 0.0


class Blocked:
    def __init__(self, source="terrain"):
        self.source = source


class OnTerrain:
    def __init__(self, terrain_type=None):
        self.terrain_type = terrain_type
        self.previous_terrain = None
