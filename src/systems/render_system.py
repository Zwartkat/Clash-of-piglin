from components.case import Case
from config.constants import Animation, Direction
from core.event_bus import EventBus
from core.iterator_system import IteratingProcessor
from components.sprite import Sprite
from components.position import Position
from components.velocity import Velocity

from core.config import Config

from events.event_move import EventMoveTo

import esper
import pygame


class RenderSystem(IteratingProcessor):

    def __init__(
        self,
        screen: pygame.Surface,
        map: list[list[Case]] = [],
        sprites: dict[str, pygame.Surface] = {},
    ):
        super().__init__(Position, Sprite)
        self.screen: pygame.Surface = screen
        self.map: list[list[Case]] = map
        # self.sprites : dict[CaseType, pygame.Surface] = {}
        self.sprites: dict[str, pygame.Surface] = sprites

    def show_map(self) -> None:
        """
        Draws the game map on the screen using the provided sprites for each terrain type.
        """
        self.screen.fill((0, 0, 0))

        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                tile: Case = self.map[y][x]
                sprite = self.sprites.get(tile.type, self.sprites.get("Netherrack"))

                if tile.type != "Lava":
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

            direction: Direction = sprite.current_direction

            if abs(velocity.x) > abs(velocity.y):
                if velocity.x > 0:
                    direction = Direction.RIGHT
                else:
                    direction = Direction.LEFT
            else:
                if velocity.y > 0:
                    direction = Direction.DOWN
                else:
                    direction = Direction.UP

            sprite.set_animation(Animation.WALK, direction)
