import esper
from components.position import Position
from components.velocity import Velocity
from core.iterator_system import IteratingProcessor


class MovementSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Position, Velocity)

    def process_entity(self, ent, dt, pos, vel):
        pos.x += vel.x * dt
        pos.y += vel.y * dt
