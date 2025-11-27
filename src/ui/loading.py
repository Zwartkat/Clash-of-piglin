import pygame
import esper
import math

from core.ecs.event_bus import EventBus
from events.loading_events import (
    LoadingStartEvent,
    LoadingProgressEvent,
    LoadingFinishEvent,
)


class LoadingUISystem(esper.Processor):
    """Loading screen with expanding square animation (Minecraft-style).

    Displays a smooth loading screen with:
    - Expanding square that grows with progress
    - Percentage display at center
    - Progress bar at bottom
    - Color evolution from dark to bright
    """

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        """Initialize the loading screen system.

        Args:
            screen: Pygame surface to render the loading screen on
            font: Font for rendering text messages
        """
        super().__init__()
        self.screen = screen
        self.font = font
        self.active = False
        self.progress = 0.0
        self.target_progress = 0.0
        self.message = "Chargement..."
        self.animation_time = 0.0

        event_bus = EventBus.get_event_bus()
        event_bus.subscribe(LoadingStartEvent, self._on_start)
        event_bus.subscribe(LoadingProgressEvent, self._on_progress)
        event_bus.subscribe(LoadingFinishEvent, self._on_finish)

    def _on_start(self, event: LoadingStartEvent):
        """Handle loading start event.

        Args:
            event: LoadingStartEvent containing initial message
        """
        self.active = True
        self.progress = 0.0
        self.target_progress = 0.0
        self.message = event.message

    def _on_progress(self, event: LoadingProgressEvent):
        """Handle loading progress update event.

        Args:
            event: LoadingProgressEvent with progress value (0.0-1.0) and optional message
        """
        self.active = True
        self.target_progress = event.progress
        if event.message:
            self.message = event.message

    def _on_finish(self, event: LoadingFinishEvent):
        """Handle loading completion event.

        Args:
            event: LoadingFinishEvent indicating success or failure
        """
        self.target_progress = 1.0
        self.message = "Terminé!" if event.success else "Échoué"

    def process(self, dt: float):
        """Render the loading screen with animated progress.

        Args:
            dt: Delta time since last frame in seconds
        """
        if not self.active:
            return

        self.animation_time += dt

        # Smooth animation
        if self.progress < self.target_progress:
            self.progress += (self.target_progress - self.progress) * 5.0 * dt
            self.progress = min(self.progress, self.target_progress)

        # Black background
        w, h = self.screen.get_size()
        self.screen.fill((15, 15, 20))

        center_x, center_y = w // 2, h // 2
        max_size = min(w, h) * 0.35
        current_size = max_size * self.progress

        # Outer square (border)
        border = 3
        outer_rect = pygame.Rect(
            center_x - current_size / 2 - border,
            center_y - current_size / 2 - border,
            current_size + border * 2,
            current_size + border * 2,
        )
        pygame.draw.rect(self.screen, (80, 80, 80), outer_rect, border_radius=8)

        # Inner square (fill)
        if current_size > 0:
            inner_rect = pygame.Rect(
                center_x - current_size / 2,
                center_y - current_size / 2,
                current_size,
                current_size,
            )
            green = int(80 + self.progress * 140)
            blue = int(100 + self.progress * 50)
            pygame.draw.rect(
                self.screen, (40, green, blue), inner_rect, border_radius=6
            )

        # Message above square
        label = self.font.render(self.message, True, (220, 220, 220))
        label_x = center_x - label.get_width() // 2
        label_y = center_y - max_size / 2 - 60
        self.screen.blit(label, (label_x, label_y))

        # Percentage at center
        percent_text = f"{int(self.progress * 100)}%"
        percent_font = pygame.font.Font(None, 56)
        percent = percent_font.render(percent_text, True, (255, 255, 255))
        percent_x = center_x - percent.get_width() // 2
        percent_y = center_y - percent.get_height() // 2

        # Shadow
        shadow = percent_font.render(percent_text, True, (0, 0, 0))
        self.screen.blit(shadow, (percent_x + 3, percent_y + 3))
        self.screen.blit(percent, (percent_x, percent_y))

        # Progress bar at bottom
        bar_y = h - 50
        bar_width = int(w * 0.6)
        bar_x = (w - bar_width) // 2

        pygame.draw.rect(
            self.screen, (40, 40, 45), (bar_x, bar_y, bar_width, 8), border_radius=4
        )

        fill_width = int(bar_width * self.progress)
        if fill_width > 0:
            pygame.draw.rect(
                self.screen,
                (60, 150 + int(self.progress * 70), 130),
                (bar_x, bar_y, fill_width, 8),
                border_radius=4,
            )
