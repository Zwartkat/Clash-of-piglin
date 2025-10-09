from enums.entity.animation import *
from enums.entity.orientation import *
from enums.entity.direction import *
from core.config import Config
import pygame


class Sprite:
    def __init__(
        self,
        sprite_sheet: str,
        frame_width: int,
        frame_height: int,
        animations: dict[Animation, dict[Direction, list[int]]],
        frame_duration: float,
        sprite_size: tuple[int] = None,
        spritesheet_direction: Orientation = Orientation.HORIZONTAL,
        default_animation: Animation = Animation.IDLE,
        default_direction: Direction = Direction.DOWN,
        priority: int = 0,
    ):
        """A sprite component that handles animations from a spritesheet.

        Args:
            sprite_sheet (str): Path to the spritesheet image.
            frame_width (int): Width of each frame in the spritesheet.
            frame_height (int): Height of each frame in the spritesheet.
            animations (dict[Animation,dict[Direction,list[int]]]): A dictionary defining the animations and their frames.
            frame_duration (float): Duration of each frame in seconds.
            sprite_size (tuple[int]) : Size to display the sprite
            spritesheet_direction (Orientation, optional): Orientation of the spritesheet. Defaults to Orientation.HORIZONTAL.
            default_animation (Animation, optional): The default animation to play. Defaults to Animation.IDLE.
            default_direction (Direction, optional): The default direction to face. Defaults to Direction.DOWN.
            priority (int) : Layer of the sprite. Defaults to 0.
        """
        self.sprite_sheet = sprite_sheet
        self.frame_width: int = frame_width
        self.frame_height: int = frame_height
        self.animations: dict[Animation, dict[Direction, list[int]]] = animations
        self.frame_duration: int = frame_duration
        self.sprite_size: int = (
            sprite_size if sprite_size else (frame_width, frame_height)
        )
        self.sprite_sheet_direction: Orientation = spritesheet_direction
        self.current_animation: Animation = default_animation
        self.current_direction: Direction = default_direction
        self.current_frame_index: int = 0
        self.delta_time: float = 0
        self.priority: int = priority

        self.image: pygame.Surface = None
        self.frames: list[pygame.Surface] = []

    def copy(sprite: "Sprite"):
        return Sprite(
            sprite.sprite_sheet,
            sprite.frame_width,
            sprite.frame_height,
            sprite.animations,
            sprite.frame_duration,
            sprite.sprite_sheet_direction,
            sprite.current_animation,
            sprite.current_direction,
        )

    def _load(self):
        self.image: pygame.Surface = pygame.image.load(
            self.sprite_sheet
        ).convert_alpha()

        # Determine the number of frames in the spritesheet
        sheet_width: int = self.image.get_width() // self.frame_width
        sheet_height: int = self.image.get_height() // self.frame_height

        outer_range: list[int] = []
        inner_range: list[int] = []

        # Extract frames based on the orientation of the spritesheet
        if self.sprite_sheet_direction == Orientation.HORIZONTAL:
            outer_range, inner_range = range(sheet_height), range(sheet_width)
        else:
            outer_range, inner_range = range(sheet_width), range(sheet_height)

        for outer in outer_range:
            for inner in inner_range:
                frame = self.image.subsurface(
                    pygame.Rect(
                        inner * self.frame_width,
                        outer * self.frame_height,
                        self.frame_width,
                        self.frame_height,
                    )
                )
                frame = pygame.transform.scale(frame, self.sprite_size)
                self.frames.append(frame)

    def set_animation(self, animation_name: Animation, direction: Direction) -> None:
        """
        Change the current animation and direction.

        Args:
            animation_name (Animation): The animation to switch to.
            direction (Direction): The direction of the animation.
        """
        if animation_name in self.animations:
            self.current_animation = animation_name
            self.current_direction = direction
            self.current_frame_index = 0

    def update(self, delta_time: float) -> None:
        """
        Update the current frame based on the elapsed time.

        Args:
            delta_time (float): The time elapsed since the last frame in seconds.
        """
        if (
            self.current_animation in self.animations
            and self.current_direction in self.animations[self.current_animation]
        ):
            frames: list[int] = self.animations[self.current_animation][
                self.current_direction
            ]
            if not frames:
                return

            # Update the frame index based on the frame duration
            self.delta_time += delta_time

            if self.delta_time >= self.frame_duration:
                self.delta_time -= self.frame_duration
                self.current_frame_index += 1

                if self.current_frame_index >= len(frames):
                    self.current_frame_index = 0

    def get_frame(self) -> pygame.Surface:
        """
        Get the current frame surface.

        Returns:
            pygame.Surface: The current frame image.
        """
        if self.image == None:
            self._load()

        return self.frames[
            self.animations[self.current_animation][self.current_direction][
                self.current_frame_index
            ]
        ]
