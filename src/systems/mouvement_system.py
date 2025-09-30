import esper
from components.position import Position
from components.velocity import Velocity
from components.effects import Slowed
from core.config import Config
from core.iterator_system import IteratingProcessor


class MovementSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Position, Velocity)

    def process_entity(self, ent: int, dt: float, pos: Position, vel: Velocity):
        effective_speed: int = self._calculate_effective_speed(ent, vel)

        if vel.x != 0 or vel.y != 0:
            magnitude = (vel.x**2 + vel.y**2) ** 0.5
            if magnitude > 0:
                normalized_x = vel.x / magnitude
                normalized_y = vel.y / magnitude

                old_x, old_y = pos.x, pos.y
                pos.x += normalized_x * effective_speed * dt
                pos.y += normalized_y * effective_speed * dt

    def _calculate_effective_speed(self, ent, vel):
        base_speed = vel.speed if vel.speed > 0 else 50  # Fallback

        speed_modifier = 1.0
        if esper.has_component(ent, Slowed):
            slowed = esper.component_for_entity(ent, Slowed)
            speed_modifier *= slowed.factor

        effective_speed = base_speed * speed_modifier * Config.TILE_SIZE()

        return effective_speed
