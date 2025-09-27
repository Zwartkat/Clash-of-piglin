from components.case import Case
from components.collider import Collider
from components.health import Health
from components.selection import Selection
from config.constants import Animation, Direction
from core.event_bus import EventBus
from core.iterator_system import IteratingProcessor
from components.sprite import Sprite
from components.position import Position
from components.velocity import Velocity

from core.config import Config
from config.constants import CaseType

from events.event_move import EventMoveTo

import esper
import pygame


class RenderSystem(IteratingProcessor):

    def __init__(
        self,
        screen: pygame.Surface,
        map: list[list[Case]] = [],
        sprites: dict[CaseType, pygame.Surface] = {},
    ):
        super().__init__(Position, Sprite)
        self.screen: pygame.Surface = screen
        self.map: list[list[Case]] = map
        # self.sprites : dict[CaseType, pygame.Surface] = {}
        self.sprites: dict[CaseType, pygame.Surface] = sprites

    def show_map(self) -> None:
        """
        Draws the game map on the screen using the provided sprites for each terrain type.
        """
        self.screen.fill((0, 0, 0))

        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                tile: Case = self.map[y][x]
                sprite = self.sprites.get(tile.type, self.sprites.get("Netherrack"))

                if tile.type != CaseType.LAVA:
                    pos_x = x * 32  # To be replaced by TILE_SIZE constant
                    pos_y = y * 32  # To be replaced by TILE_SIZE constant
                    self.screen.blit(sprite, (pos_x, pos_y))

    def process_entity(self, ent, dt, position: Position, sprite: Sprite):
        """
        For each entity with a Position and Sprite component, update the sprite animation and draw it on the screen at the entity's position.

        Args:
            ent (int): The entity ID.
            dt (float): The delta time since the last frame.
            position (Position): The Position component of the entity.
            sprite (Sprite): The Sprite component of the entity.
        """
        sprite.update(dt)
        frame: pygame.Surface = sprite.get_frame()
        if frame:
            x = position.x
            y = position.y
            if sprite.current_animation != Animation.NONE:
                x = position.x - (frame.get_width() / 2)
                y = position.y - (frame.get_height() / 2)
                frame = pygame.transform.scale(
                    frame, (Config.get("tile_size"), Config.get("tile_size"))
                )
                if esper.has_component(ent, Selection):
                    selection: Selection = esper.component_for_entity(ent, Selection)
                    color = (0, 255, 0) if selection.is_selected else (255, 0, 0)

                    self._draw_diamond(position, color)

                self._draw_health_bar(position, esper.component_for_entity(ent, Health))

            self.screen.blit(frame, (x, y))

    def animate_move(self, event: EventMoveTo):
        """
        Animate entity who moves by changing its sprite animation based on its velocity direction.

        Args:
            event (EventMoveTo): An event containing the entity that moved.
        """
        if esper.has_component(event.entity, Velocity) and esper.has_component(
            event.entity, Sprite
        ):
            velocity: Velocity = esper.component_for_entity(event.entity, Velocity)
            sprite: Sprite = esper.component_for_entity(event.entity, Sprite)

            direction: Direction = self._get_direction_from_velocity(velocity)

            sprite.set_animation(Animation.WALK, direction)

    def _get_direction_from_velocity(self, velocity: Velocity) -> Direction:
        """
        Determine the primary direction of movement based on the velocity components.

        Args:
            velocity (Velocity): The velocity component containing x and y speed.

        Returns:
            Direction: The primary direction of movement (UP, DOWN, LEFT, RIGHT).
        """
        if abs(velocity.x) > abs(velocity.y):
            return Direction.RIGHT if velocity.x > 0 else Direction.LEFT
        else:
            return Direction.DOWN if velocity.y > 0 else Direction.UP

    def _draw_diamond(self, position: Position, color):
        """
        Draw a diamond shape at the given position with the specified color.

        Args:
            position (Position): Position of the linked entity.
            color (_type_): Color of the diamond.
        """
        x: int = position.x
        y: int = position.y - Config.TILE_SIZE() // 2

        diamond_points: list[tuple[int]] = [
            (x, y - 10),  # Top
            (x + 2, y - 8),  # right
            (x, y - 6),  # bottom
            (x - 2, y - 8),  # left
        ]

        pygame.draw.polygon(self.screen, color, diamond_points)
        # pygame.draw.polygon(self.screen, (0, 0, 0), diamond_points, 1)

    def _draw_health_bar(self, position: Position, health: Health):
        """
        Draw a health bar above the entity's position.

        Args:
            position (Position): Position of the linked entity.
            health (Health): Health of the linked entity.
        """
        bar_width: int = Config.TILE_SIZE() - Config.TILE_SIZE() // 2
        bar_height: int = 4

        bar_x: int = int(position.x - bar_width // 2)
        bar_y: int = int(position.y - Config.TILE_SIZE() // 2 - 3)

        # Border of the health bar
        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2),
        )

        # Red part of health bar (HP lost)
        if health.remaining < health.full and health.remaining > 0:
            pygame.draw.rect(
                self.screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height)
            )

        # Green part of health bar (HP remaining)
        hp_ratio = max(0, health.remaining / health.full)  # between 0 and 1
        green_width = int(bar_width * hp_ratio)
        if green_width > 0:
            pygame.draw.rect(
                self.screen, (0, 255, 0), (bar_x, bar_y, green_width, bar_height)
            )
