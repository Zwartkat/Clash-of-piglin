from core.iterator_system import IteratingProcessor
from components.sprite import Sprite
from components.position import Position

import esper
import pygame


class RenderSystem(IteratingProcessor):

    screen: pygame.Surface

    def __init__(self, screen):
        super().__init__(Position, Sprite)
        self.screen = screen

    def process_entity(self, ent, dt, position: Position, sprite: Sprite):
        sprite.update(dt)

        frame: pygame.Surface = sprite.get_frame()
        if frame:
            self.screen.blit(
                frame, (position.x, position.y)
            )  # (position.x - (frame.get_width()/2) décale le sprite pour qu'il soit centré sur la position
