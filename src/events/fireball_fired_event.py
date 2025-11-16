from core.ecs.event import Event
from components.base.position import Position


class FireballFiredEvent(Event):
    """Event emitted when a Ghast fires an fireball"""

    def __init__(self, shooter_id: int, start_pos: Position, target_pos: Position):
        """
        Initialize fireball fired event.

        Args:
            shooter_id (int): ID of the entity that fired the fireball
            start_pos (Position): Starting position of the fireball
            target_pos (Position): Target position of the fireball
        """
        self.shooter_id = shooter_id
        self.start_pos = start_pos
        self.target_pos = target_pos
