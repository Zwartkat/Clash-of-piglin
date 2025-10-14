import esper
import pygame
import math
from typing import Tuple

from core.ecs.iterator_system import IteratingProcessor
from core.ecs.event_bus import EventBus
from components.arrow import Arrow
from components.base.position import Position
from events.arrow_fired_event import ArrowFiredEvent
from factories.entity_factory import EntityFactory


class ArrowSystem(IteratingProcessor):
    """System that handles arrow movement and rendering for Crossbowman attacks"""

    def __init__(self, render_system):
        super().__init__(Arrow, Position)
        self.render_system = render_system

        # Subscribe to arrow fired events
        EventBus.get_event_bus().subscribe(ArrowFiredEvent, self.on_arrow_fired)

        # Create authentic Minecraft-style arrow sprite
        self.arrow_surface = pygame.Surface((16, 4), pygame.SRCALPHA)
        # Wood shaft (brown)
        pygame.draw.rect(self.arrow_surface, (139, 69, 19), (2, 1, 10, 2))
        # Iron arrowhead (gray)
        pygame.draw.polygon(
            self.arrow_surface, (169, 169, 169), [(12, 0), (16, 2), (12, 4)]
        )
        # Feathers (white/light gray)
        pygame.draw.rect(self.arrow_surface, (245, 245, 245), (0, 1, 2, 2))

    def on_arrow_fired(self, event: ArrowFiredEvent):
        """
        Handle arrow fired event by creating a new arrow entity.

        Args:
            event (ArrowFiredEvent): The arrow fired event containing shooter and target info
        """
        arrow_component = Arrow(
            event.start_pos, event.target_pos, speed=400.0, lifetime=3.0
        )
        position_component = Position(event.start_pos.x, event.start_pos.y)
        EntityFactory.create(arrow_component, position_component)

    def process_entity(self, ent: int, dt: float, arrow: Arrow, position: Position):
        """
        Update individual arrow position and render it.

        Args:
            ent (int): The arrow entity ID
            dt (float): Delta time since last frame
            arrow (Arrow): The arrow component containing flight data
            position (Position): The arrow's current position component
        """
        arrow.current_time += dt

        # Remove arrow if expired or reached target
        if (
            arrow.current_time >= arrow.lifetime
            or arrow.current_time >= arrow.flight_time
        ):
            esper.delete_entity(ent)
            return

        # Update arrow position
        distance_traveled = arrow.speed * arrow.current_time
        position.x = arrow.start_pos.x + arrow.direction_x * distance_traveled
        position.y = arrow.start_pos.y + arrow.direction_y * distance_traveled

        self._draw_arrow(position, arrow)

    def _draw_arrow(self, position: Position, arrow: Arrow):
        """
        Draw arrow on screen with proper rotation using RenderSystem.

        Args:
            position (Position): Current arrow position in world coordinates
            arrow (Arrow): Arrow component containing direction data
        """
        angle = math.degrees(math.atan2(arrow.direction_y, arrow.direction_x))
        rotated_arrow = pygame.transform.rotate(self.arrow_surface, -angle)

        # Use RenderSystem.draw_surface() which handles camera and zoom automatically
        self.render_system.draw_surface(rotated_arrow, position.x - 8, position.y - 2)
