import esper
import pygame
import math
from typing import Tuple

from core.iterator_system import IteratingProcessor
from core.event_bus import EventBus
from components.arrow import Arrow
from components.position import Position
from events.arrow_fired_event import ArrowFiredEvent
from systems.entity_factory import EntityFactory
from core.camera import CAMERA


class ArrowSystem(IteratingProcessor):
    """System that handles arrow movement and rendering for Crossbowman attacks"""

    def __init__(self, screen: pygame.Surface):
        super().__init__(Arrow, Position)
        self.screen = screen

        # Subscribe to arrow fired events
        EventBus.get_event_bus().subscribe(ArrowFiredEvent, self.on_arrow_fired)

        # Create Minecraft-style arrow sprite
        self.arrow_surface = pygame.Surface((16, 4), pygame.SRCALPHA)
        pygame.draw.rect(self.arrow_surface, (101, 67, 33), (2, 1, 10, 2))  # Wood shaft
        pygame.draw.polygon(
            self.arrow_surface, (169, 169, 169), [(12, 0), (16, 2), (12, 4)]
        )  # Metal tip
        pygame.draw.rect(self.arrow_surface, (220, 220, 220), (0, 1, 2, 2))  # Feathers

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
        Draw arrow on screen with trail effect and proper rotation.

        Args:
            position (Position): Current arrow position in world coordinates
            arrow (Arrow): Arrow component containing direction data
        """
        angle = math.degrees(math.atan2(arrow.direction_y, arrow.direction_x))
        rotated_arrow = pygame.transform.rotate(self.arrow_surface, -angle)

        if CAMERA.is_visible(position.x - 16, position.y - 16, 32, 32):
            screen_x, screen_y = CAMERA.apply(position.x, position.y)

            # Draw trail for better visibility
            for i in range(3):
                trail_x = position.x - arrow.direction_x * (i * 8)
                trail_y = position.y - arrow.direction_y * (i * 8)
                trail_screen_x, trail_screen_y = CAMERA.apply(trail_x, trail_y)

                alpha = 100 - (i * 30)
                if alpha > 0:
                    trail_surface = pygame.Surface((2, 2), pygame.SRCALPHA)
                    trail_surface.fill((255, 255, 255, alpha))
                    self.screen.blit(
                        trail_surface, (trail_screen_x - 1, trail_screen_y - 1)
                    )

            # Draw arrow with zoom
            rect = rotated_arrow.get_rect(center=(screen_x, screen_y))
            zoom = CAMERA.zoom_factor
            if zoom != 1.0:
                scaled_size = (int(rect.width * zoom), int(rect.height * zoom))
                rotated_arrow = pygame.transform.scale(rotated_arrow, scaled_size)
                rect = rotated_arrow.get_rect(center=(screen_x, screen_y))

            self.screen.blit(rotated_arrow, rect)
