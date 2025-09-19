from core.iterator_system import IteratingProcessor
from components.position import Position
from components.velocity import Velocity


class CollisionSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Position, Velocity)

    def process_entity(self, ent, dt, pos, vel):
        # Placeholder for collision logic
        pass
