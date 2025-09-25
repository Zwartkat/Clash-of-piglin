from config.constants import Orientation, Animation, Direction
import pygame


class Sprite:
    def __init__(
        self,
        sprite_sheet: str,
        frame_width: int,
        frame_height: int,
        animations: dict[Animation, dict[Direction, list[int]]],
        frame_duration: float,
        spritesheet_direction: Orientation = Orientation.HORIZONTAL,
        default_animation: Animation = Animation.IDLE,
        default_direction: Direction = Direction.DOWN,
    ):
        """A sprite component that handles animations from a spritesheet.

        Args:
            sprite_sheet (str): Path to the spritesheet image.
            frame_width (int): Width of each frame in the spritesheet.
            frame_height (int): Height of each frame in the spritesheet.
            animations (dict[Animation,dict[Direction,list[int]]]): A dictionary defining the animations and their frames.
            frame_duration (float): Duration of each frame in seconds.
            spritesheet_direction (Orientation, optional): Orientation of the spritesheet. Defaults to Orientation.HORIZONTAL.
            default_animation (Animation, optional): The default animation to play. Defaults to Animation.IDLE.
            default_direction (Direction, optional): The default direction to face. Defaults to Direction.DOWN.
        """
        self.image: pygame.Surface = pygame.image.load(sprite_sheet).convert_alpha()
        self.frame_width: int = frame_width
        self.frame_height: int = frame_height
        self.animations: dict[Animation, dict[Direction, list[int]]] = animations
        self.frame_duration: int = frame_duration
        self.current_animation: Animation = default_animation
        self.current_direction: Direction = default_direction
        self.current_frame_index: int = 0
        self.frames: list[pygame.Surface] = []
        self.delta_time: float = 0

        # Determine the number of frames in the spritesheet
        sheet_width: int = self.image.get_width() // frame_width
        sheet_height: int = self.image.get_height() // frame_height

        outer_range: list[int] = []
        inner_range: list[int] = []

        # Extract frames based on the orientation of the spritesheet
        if spritesheet_direction == Orientation.HORIZONTAL:
            outer_range, inner_range = range(sheet_height), range(sheet_width)
        else:
            outer_range, inner_range = range(sheet_width), range(sheet_height)

        for outer in outer_range:
            for inner in inner_range:
                frame = self.image.subsurface(
                    pygame.Rect(
                        inner * frame_width,
                        outer * frame_height,
                        frame_width,
                        frame_height,
                    )
                )
                frame = pygame.transform.scale(frame, (32, 32))
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

            # Quand assez de temps est passé, on change de frame
            if self.delta_time >= self.frame_duration:
                self.delta_time -= self.frame_duration  # on garde le "reste"
                self.current_frame_index += 1

                # Boucler si on dépasse
                if self.current_frame_index >= len(frames):
                    self.current_frame_index = 0

    def get_frame(self) -> pygame.Surface:
        """
        Get the current frame surface.

        Returns:
            pygame.Surface: The current frame image.
        """
        return self.frames[
            self.animations[self.current_animation][self.current_direction][
                self.current_frame_index
            ]
        ]
