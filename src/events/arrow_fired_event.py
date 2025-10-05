from core.event import Event
from components.position import Position


class ArrowFiredEvent(Event):
    """Event emitted when a Crossbowman fires an arrow"""

    def __init__(self, shooter_id: int, start_pos: Position, target_pos: Position):
        """
        Initialize arrow fired event.

        Args:
            shooter_id (int): ID of the entity that fired the arrow
            start_pos (Position): Starting position of the arrow
            target_pos (Position): Target position of the arrow
        """
        self.shooter_id = shooter_id
        self.start_pos = start_pos
        self.target_pos = target_pos
