from core.component import Component
from components.position import Position


class Arrow(Component):
    """Component representing an arrow fired by a Crossbowman"""

    def __init__(
        self,
        start_pos: Position,
        target_pos: Position,
        speed: float = 200.0,
        lifetime: float = 2.0,
    ):
        """
        Initialize an arrow component.

        Args:
            start_pos (Position): Starting position of the arrow
            target_pos (Position): Target position the arrow flies toward
            speed (float): Arrow speed in pixels per second
            lifetime (float): Maximum lifetime of the arrow in seconds
        """
        self.start_pos = Position(start_pos.x, start_pos.y)
        self.target_pos = Position(target_pos.x, target_pos.y)
        self.speed = speed
        self.lifetime = lifetime
        self.current_time = 0.0

        # Calculate arrow direction
        dx = target_pos.x - start_pos.x
        dy = target_pos.y - start_pos.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance > 0:
            self.direction_x = dx / distance
            self.direction_y = dy / distance
        else:
            self.direction_x = 0
            self.direction_y = 0

        # Calculate estimated flight time
        self.flight_time = distance / speed if speed > 0 else 0
