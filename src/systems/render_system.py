from typing import Tuple
from components.team import Team
from core.camera import CAMERA, Camera
from components.case import Case
from components.health import Health
from components.map import Map
from components.selection import Selection
from core.event_bus import EventBus
from core.iterator_system import IteratingProcessor
from components.sprite import Sprite
from components.position import Position
from components.velocity import Velocity

from core.config import Config

from core.services import Services
from enums.case_type import *
from enums.animation import *
from enums.orientation import *
from enums.direction import *

from events.attack_event import AttackEvent
from events.event_move import EventMoveTo

import esper
import pygame

from events.stop_event import StopEvent


class RenderSystem(IteratingProcessor):

    def __init__(
        self,
        screen: pygame.Surface,
        map: Map,
        sprites: dict[CaseType, pygame.Surface] = {},
    ):
        super().__init__(Position, Sprite)
        self.screen: pygame.Surface = screen
        self.map: list[list[Case]] = map.tab
        self.sprites: dict[CaseType, pygame.Surface] = sprites
        self.entities = []

        EventBus.get_event_bus().subscribe(StopEvent, self.animate_idle)
        EventBus.get_event_bus().subscribe(EventMoveTo, self.animate_move)
        EventBus.get_event_bus().subscribe(AttackEvent, self.animate_attack)

    def process(self, dt):

        entities_comps: list = esper.get_components(Position, Sprite)
        sprite_index: int = self.components.index(Sprite)

        if self.entities != entities_comps:
            entities_comps = sorted(
                entities_comps, key=lambda ent: (ent[1][sprite_index]).priority
            )
            self.entities = entities_comps

        for ent, comps in self.entities:
            self.process_entity(ent, dt, *comps)

    def process_entity(self, ent, dt, position: Position, sprite: Sprite) -> None:
        """
        For each entity with a Position and Sprite component, update the sprite animation and draw it on the screen at the entity's position.

        Args:
            ent (int): The entity ID.
            dt (float): The delta time since the last frame.
            position (Position): The Position component of the entity.
            sprite (Sprite): The Sprite component of the entity.
        """

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
                if Services.player_manager.current_player == (
                    esper.component_for_entity(ent, Team)
                ).team_id and esper.has_component(ent, Selection):
                    selection: Selection = esper.component_for_entity(ent, Selection)
                    color = (0, 255, 0) if selection.is_selected else (255, 0, 0)

                    self._draw_diamond(position, color)

                self._draw_health_bar(
                    ent, position, esper.component_for_entity(ent, Health)
                )

            self.draw_surface(frame, x, y)
        sprite.update(dt)

    def show_map(self) -> None:
        """
        Draws the game map on the screen using the provided sprites for each terrain type.
        """
        self.screen.fill((67, 37, 36))
        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                tile: Case = self.map[y][x]
                sprite: pygame.Surface = self.sprites.get(
                    tile.type, self.sprites.get("Netherrack")
                )

                if tile.type != CaseType.LAVA:
                    pos_x = x * Config.get("tile_size")
                    pos_y = y * Config.get("tile_size")
                    self.draw_surface(sprite, pos_x, pos_y)

    def _set_animation(self, ent: int, animation: Animation):
        if esper.has_component(ent, Velocity) and esper.has_component(ent, Sprite):
            velocity: Velocity = esper.component_for_entity(ent, Velocity)
            sprite: Sprite = esper.component_for_entity(ent, Sprite)

            if velocity.x != 0 and velocity.y != 0:
                direction: Direction = self._get_direction_from_velocity(velocity)
            else:
                direction = sprite.current_direction

            sprite.set_animation(animation, direction)

    def animate_idle(self, event: StopEvent) -> None:
        """
        Animate entity who stopping by changing its sprite animation to idle.

        Args:
            event (StopEvent): An event containing the entity that stop moving.
        """
        self._set_animation(event.entity, Animation.IDLE)

    def animate_move(self, event: EventMoveTo) -> None:
        """
        Animate entity who moves by changing its sprite animation based on its velocity direction.

        Args:
            event (EventMoveTo): An event containing the entity that moved.
        """
        self._set_animation(event.entity, Animation.WALK)

    def animate_attack(self, event: AttackEvent):
        """
        Animate entity who attack by changing its sprite animation on attack

        Args:
            event (AttackEvent): An event emit before an attack
        """
        self._set_animation(event.fighter, Animation.ATTACK)
        self._set_animation(event.target, Animation.ATTACK)

    def draw_surface(
        self, image: pygame.Surface, x: int = None, y: int = None
    ) -> tuple[int] | None:
        """Draws a surface (image) considering the camera position and zoom.

        Args:
            image (pygame.Surface): The image (sprite) to render.
            x (int, optional): World x position. If None → taken from `image.get_rect()`.
            y (int, optional): World y position. If None → taken from `image.get_rect()`.

        Returns:
            tuple[int]: The final (x, y) position of the image after applying the camera transform. None if there is not visible.
        """

        rect: pygame.Rect = image.get_rect()
        x = x if x else rect.x
        y = y if y else rect.y

        if CAMERA.is_visible(x, y, rect.width, rect.height):
            pos: Tuple[int] = CAMERA.apply(x, y)
            zoom: float = CAMERA.zoom_factor
            image = pygame.transform.scale(
                image,
                (round(rect.width * zoom + 0.9999), round(rect.height * zoom + 0.9999)),
            )

            self.screen.blit(image, (pos[0], pos[1]))
            return pos
        return None

    def draw_rect(self, rect_value, color: Tuple[int] = (0, 0, 0)):
        """Draws a rectangle considering the camera position and zoom.


        Args:
            rect_value (tuple[int]): (x, y, width, height) in world coordinates.
            color (Tuple[int], optional): RGB color of the rectangle (default: black).
        """

        if CAMERA.is_visible(
            rect_value[0], rect_value[1], rect_value[2], rect_value[3]
        ):
            x, y = CAMERA.apply(rect_value[0], rect_value[1])
            zoom = CAMERA.zoom_factor
            rect = pygame.Rect(
                x,
                y,
                round(rect_value[2] * zoom + 0.9999),
                round(rect_value[3] * zoom + 0.9999),
            )
            pygame.draw.rect(self.screen, color, rect)

    def draw_polygon(self, sequence: list[tuple[int]], color: Tuple[int] = (0, 0, 0)):
        """Draws a polygon considering the camera position.

        Args:
            sequence (list[tuple[int]]): List of points [(x1, y1), (x2, y2), ...] in world coordinates.
            color (Tuple[int], optional): RGB color of the polygon (default: black).
        """

        min_x = min(x for x, y in sequence)
        max_x = max(x for x, y in sequence)
        min_y = min(y for x, y in sequence)
        max_y = max(y for x, y in sequence)

        if CAMERA.is_visible(min_x, min_y, max_x - min_x, max_y - min_y):

            camera_sequence: list[tuple[int]] = []
            for x, y in sequence:
                camera_sequence.append(CAMERA.apply(x, y))
            pygame.draw.polygon(self.screen, color, camera_sequence)

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
        self.draw_polygon(diamond_points, color)

    def _draw_health_bar(self, ent: int, position: Position, health: Health):
        """
        Draw a health bar above the entity's position.

        Args:
            ent (int): Entity ID
            position (Position): Position of the linked entity.
            health (Health): Health of the linked entity.
        """
        # Vérification simple de la santé
        if not health or health.full <= 0:
            return

        bar_width: int = Config.TILE_SIZE() - Config.TILE_SIZE() // 2
        bar_height: int = 4

        bar_x: int = int(position.x - bar_width // 2)
        bar_y: int = int(position.y - Config.TILE_SIZE() // 2 - 3)

        # Border of the health bar (black background)
        self.draw_rect((bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), (0, 0, 0))

        # Couleurs universelles pour toutes les équipes
        health_color = (50, 200, 50)  # Vert pour la vie
        damage_color = (200, 50, 50)  # Rouge pour les dégâts

        # Background of health bar (dark gray)
        self.draw_rect((bar_x, bar_y, bar_width, bar_height), (60, 60, 60))

        # Red part for lost health
        if health.remaining < health.full:
            self.draw_rect((bar_x, bar_y, bar_width, bar_height), damage_color)

        # Debug temporaire
        if health.remaining == 0 and health.full > 0:
            print(f"Unit {ent} has 0/{health.full} HP!")

        # Green part for remaining health
        hp_ratio = max(0, min(1.0, health.remaining / health.full))
        health_width = int(bar_width * hp_ratio)
        if health_width > 0:
            self.draw_rect((bar_x, bar_y, health_width, bar_height), health_color)
