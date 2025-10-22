import math
from core.accessors import get_config
from core.ecs.component import Component


class Position(Component):

    def __init__(self, x: int = 1, y: int = 1):
        self.x = x
        self.y = y

    @classmethod
    def initFromModel(cls, model):
        if not isinstance(model, cls):
            raise TypeError("model must be a Position instance")
        return cls(model.x, model.y)

    def getX(self) -> int:
        return self.x

    def getY(self) -> int:
        return self.y

    def setX(self, value: int) -> None:
        self.x = value

    def setY(self, value: int) -> None:
        self.y = value

    def to_grid(self):
        from core.services import Services

        tile_size = Services.config.get("tile_size")
        return (int(self.x // tile_size), int(self.y // tile_size))

    @staticmethod
    def from_grid(pos: tuple[float]):

        from core.services import Services

        tile_size = get_config().get("tile_size")
        return Position(int(pos[0] * tile_size), int(pos[1] * tile_size))

    @staticmethod
    def to_tuple(pos: "Position") -> tuple[int, int]:
        return (int(pos.x), int(pos.y))

    def direction_to(self, target):
        dx, dy = target.x - self.x, target.y - self.y
        dist = self.distance_to(target)
        if dist == 0:
            return 0, 0
        return dx / dist, dy / dist

    def distance_to(self, target):
        dx, dy = target.x - self.x, target.y - self.y
        return math.hypot(dx, dy)

    def __str__(self):
        return f"Position of coordonates {self.x}, {self.y}.\n"
