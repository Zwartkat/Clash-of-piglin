import esper
from components.position import Position
from components.velocity import Velocity

class MovementSystem(esper.Processor):
    def process(self, dt):
        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            pos.x += vel.x * dt
            pos.y += vel.y * dt