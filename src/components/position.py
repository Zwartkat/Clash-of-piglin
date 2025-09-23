from core.component import Component


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

    def __str__(self):
        return f"Position of coordonates {self.x}, {self.y}.\n"
