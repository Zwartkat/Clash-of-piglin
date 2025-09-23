import pygame


class Sprite:
    def __init__(
        self,
        sprite_sheet,
        frame_with,
        frame_height,
        animations,
        frame_duration,
        spritesheet_direction="horizontal",
    ):
        self.image = pygame.image.load(sprite_sheet).convert_alpha()
        self.frame_with = frame_with
        self.frame_height = frame_height
        self.animations = animations
        self.frame_duration = frame_duration
        self.current_animation = "idle"
        self.current_direction = "down"
        self.current_frame_index = 0
        self.frames = []

        sheet_width = self.image.get_width() // frame_with
        sheet_height = self.image.get_height() // frame_height

        if spritesheet_direction == "horizontal":
            for y in range(sheet_height):
                for x in range(sheet_width):
                    frame = self.image.subsurface(
                        pygame.Rect(
                            x * frame_with, y * frame_height, frame_with, frame_height
                        )
                    )
                    frame = pygame.transform.scale(frame, (32, 32))
                    self.frames.append(frame)
        else:
            for x in range(sheet_width):
                for y in range(sheet_height):
                    frame = self.image.subsurface(
                        pygame.Rect(
                            x * frame_with, y * frame_height, frame_with, frame_height
                        )
                    )
                    frame = pygame.transform.scale(frame, (32, 32))
                    self.frames.append(frame)

    def set_animation(self, animation_name, direction):
        if animation_name in self.animations:
            self.current_animation = animation_name
            self.current_direction = direction
            self.current_frame_index = self.animations[animation_name][direction][0]

    def update(self, delta_time):
        if self.current_animation in self.animations:
            frames = self.animations[self.current_animation][self.current_direction]
            self.current_frame_index += delta_time / self.frame_duration
            if self.current_frame_index >= len(frames):
                self.current_frame_index = 0
            self.current_frame_index = int(self.current_frame_index)

    def get_frame(self):
        return self.frames[
            self.animations[self.current_animation][self.current_direction][
                self.current_frame_index
            ]
        ]
