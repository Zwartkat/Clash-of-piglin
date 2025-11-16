from core.ecs.component import Component
from components.base.position import Position


class Fireball(Component):
    """Component representing an fireball fired by a Ghast"""

    def __init__(
        self,
        start_pos: Position,
        target_pos: Position,
        speed: float = 200.0,
        lifetime: float = 2.0,
    ):
        """
        Initialize an fireball component.

        Args:
            start_pos (Position): Starting position of the fireball
            target_pos (Position): Target position the fireball flies toward
            speed (float): Fireball speed in pixels per second
            lifetime (float): Maximum lifetime of the fireball in seconds
        """
        self.start_pos = Position(start_pos.x, start_pos.y)
        self.target_pos = Position(target_pos.x, target_pos.y)
        self.speed = speed
        self.lifetime = lifetime
        self.current_time = 0.0
        self.direction_x = 0
        self.direction_y = 0