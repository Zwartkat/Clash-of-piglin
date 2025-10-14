from core.ecs.component import Component


class Velocity(Component):
    """Composant who represent the velocity of an entity"""

    x: float
    y: float
    speed: int

    def __init__(self, x: int = 0, y: int = 0, speed: int = 0):
        self.x = x
        self.y = y
        self.speed = speed
