import esper
import pygame
import math

from core.accessors import get_event_bus
from core.ecs.iterator_system import IteratingProcessor
from components.fireball import Fireball
from components.base.position import Position
from events.fireball_fired_event import FireballFiredEvent
from factories.entity_factory import EntityFactory


class FireballSystem(IteratingProcessor):
    """System that handles fireball movement and rendering for Ghast attacks"""

    def __init__(self, render_system):
        super().__init__(Fireball, Position)
        self.render_system = render_system

        # Subscribe to fireball fired events
        get_event_bus().subscribe(FireballFiredEvent, self.on_fireball_fired)

        # Create authentic Minecraft-style fireball sprite
        self.fireball_surface = pygame.Surface((16, 16), pygame.SRCALPHA)

        # Yellow center
        pygame.draw.circle(self.fireball_surface, (255, 220, 90), (8, 8), 4)

        # Orange ring
        pygame.draw.circle(self.fireball_surface, (230, 140, 40), (8, 8), 6, width=2)

        # Brown external ring
        pygame.draw.circle(self.fireball_surface, (90, 50, 30), (8, 8), 7, width=2)

        # Little red orange sparks
        spark_colors = [
            (255, 180, 40),
            (220, 120, 30),
            (200, 80, 20)
        ]

        spark_positions = [(3, 5), (12, 6), (6, 12), (10, 3)]

        for (x, y), col in zip(spark_positions, spark_colors):
            self.fireball_surface.set_at((x, y), col)


    def on_fireball_fired(self, event: FireballFiredEvent):
        """
        Handle fireball fired event by creating a new fireball entity.

        Args:
            event (FireballFiredEvent): The fireball fired event containing shooter and target info
        """

        fireball_component = Fireball(
            event.start_pos, event.target_pos, speed=400.0, lifetime=3.0
        )
        position_component = Position(event.start_pos.x, event.start_pos.y)
        EntityFactory.create(fireball_component, position_component)

    def process_entity(self, ent: int, dt: float, fireball: Fireball, position: Position):
        """
        Update individual fireball position and render it.

        Args:
            ent (int): The fireball entity ID
            dt (float): Delta time since last frame
            fireball (Fireball): The fireball component containing flight data
            position (Position): The fireball's current position component
        """

        fireball.current_time += dt

        # Remove fireball if expired or reached target
        if (fireball.current_time >= fireball.lifetime):
            esper.delete_entity(ent)
            return
        
        dx = fireball.target_pos.x - position.x
        dy = fireball.target_pos.y - position.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance < 5:
            esper.delete_entity(ent)
            return
        
        # Normalisation
        if distance > 0:
            nx = dx / distance
            ny = dy / distance
        else:
            nx, ny = 0, 0

        # Update fireball position
        position.x += nx * fireball.speed * dt
        position.y += ny * fireball.speed * dt

        self.render_system.draw_surface(self.fireball_surface, position.x - 8, position.y - 8)
