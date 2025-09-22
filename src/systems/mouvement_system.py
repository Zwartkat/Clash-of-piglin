import esper
from components.position import Position
from components.velocity import Velocity
from components.effects import Slowed, Blocked
from core.iterator_system import IteratingProcessor


class MovementSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Position, Velocity)

    def process_entity(self, ent, dt, pos, vel):
        speed_modifier = self._calculate_speed_modifier(ent)

        pos.x += vel.x * speed_modifier * dt
        pos.y += vel.y * speed_modifier * dt

    def _calculate_speed_modifier(self, ent):
        modifier = 1.0

        if esper.has_component(ent, Slowed):
            slowed = esper.component_for_entity(ent, Slowed)
            modifier *= slowed.factor

        return modifier
