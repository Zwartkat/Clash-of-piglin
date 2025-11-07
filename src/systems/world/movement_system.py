import esper
from components.base.position import Position
from components.base.velocity import Velocity
from components.gameplay.effects import Slowed
from core.config import Config
from core.ecs.iterator_system import IteratingProcessor


class MovementSystem(IteratingProcessor):
    """Moves entities based on their velocity with terrain effect modifiers."""

    def __init__(self):
        super().__init__(Position, Velocity)

    def process_entity(self, ent, dt, pos, vel):
        """
        Move entity based on velocity and apply terrain slowdown effects.

        Args:
            ent: Entity ID to move
            dt: Time passed since last frame
            pos: Entity position to update
            vel: Entity velocity for movement
        """
        effective_speed: int = self._calculate_effective_speed(ent, vel)

        if vel.x != 0 or vel.y != 0:
            magnitude = (vel.x**2 + vel.y**2) ** 0.5
            if magnitude > 0:
                # Normalize velocity and apply effective speed
                normalized_x = vel.x / magnitude
                normalized_y = vel.y / magnitude

                old_x, old_y = pos.x, pos.y
                pos.x += round(normalized_x * effective_speed * dt, 3)
                pos.y += round(normalized_y * effective_speed * dt, 3)

    def _calculate_effective_speed(self, ent, vel):
        """
        Calculate final speed with terrain effects like Soul Sand slowdown.

        Args:
            ent: Entity ID to check for slowdown effects
            vel: Entity velocity component with base speed

        Returns:
            float: Final movement speed with all effects applied
        """
        base_speed = vel.speed if vel.speed > 0 else 50  # Default speed

        speed_modifier = 1.0

        # Apply slowdown from terrain effects
        if esper.has_component(ent, Slowed):
            slowed = esper.component_for_entity(ent, Slowed)
            speed_modifier *= slowed.factor

        effective_speed = base_speed * speed_modifier * Config.TILE_SIZE()

        return effective_speed
