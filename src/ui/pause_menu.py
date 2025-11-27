"""Pause menu system."""

import pygame
import esper

from core.accessors import get_event_bus
from events.pause_events import PauseToggleEvent, ResumeGameEvent, QuitToMenuEvent
from events.resize_event import ResizeEvent
from core.config import Config
import core.options as option
from ui.options_menu import OptionsMenu


class PauseMenuSystem(esper.Processor):
    """Pause menu overlay with Minecraft-style design.

    Manages the pause state, handles input events, and renders the pause menu
    with three options: Resume, Options, and Return to Menu.
    """

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, hud_system=None):
        """Initialize the pause menu system.

        Args:
            screen: Pygame surface to render the menu on
            font: Font for rendering text
            hud_system: Reference to HUD system for pause time tracking (optional)
        """
        super().__init__()
        self.screen = screen
        self.font = font
        self.is_paused = False
        self.hud_system = hud_system
        self.menu_items = ["Reprendre", "Options", "Retour au menu"]
        self.selected_index = 0
        self.button_rects = []

        event_bus = get_event_bus()
        event_bus.subscribe(PauseToggleEvent, self._on_pause_toggle)
        event_bus.subscribe(ResizeEvent, self._on_resize)

    def _on_resize(self, event: ResizeEvent):
        """Update screen reference when display is resized."""
        self.screen = pygame.display.get_surface()

    def _on_pause_toggle(self, event: PauseToggleEvent):
        """Toggle pause state and notify HUD system.

        Args:
            event: PauseToggleEvent triggering the toggle
        """
        was_paused = self.is_paused
        self.is_paused = not self.is_paused
        self.selected_index = 0

        if self.hud_system:
            if self.is_paused and not was_paused:
                self.hud_system.hud.on_pause()
            elif not self.is_paused and was_paused:
                self.hud_system.hud.on_resume()

    def draw_button(self, surface, rect, text, hovered):
        """Draw a button with Minecraft-style appearance.

        Creates a 3D-looking button with shadow, border, and hover effects.

        Args:
            surface: Pygame surface to draw on
            rect: Button rectangle defining position and size
            text: Button label text
            hovered: Whether the button is currently hovered
        """
        base_color = (165, 165, 165) if hovered else (198, 198, 198)
        shadow_color = (60, 60, 60)
        border_color = (80, 80, 80)

        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=8)
        pygame.draw.rect(surface, base_color, rect, border_radius=8)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)

        button_font = pygame.font.Font(Config.get_assets(key="font"), 20)
        text_surf = button_font.render(text, True, (40, 40, 40))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame input events for menu navigation.

        Processes keyboard (ESC, arrows, Enter) and mouse (click, motion) events
        when the game is paused.

        Args:
            event: Pygame event to process

        Returns:
            True if the event was consumed by the menu, False otherwise
        """
        if not self.is_paused:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.is_paused = False
                if self.hud_system:
                    self.hud_system.hud.on_resume()
                get_event_bus().emit(ResumeGameEvent())
                return True
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                return True
            elif event.key == pygame.K_RETURN:
                self._handle_selection()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_index = i
                    self._handle_selection()
                    return True
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_index = i

        return False

    def _handle_selection(self):
        """Execute the action for the currently selected menu item.

        Emits appropriate events based on selection:
        - Reprendre: ResumeGameEvent
        - Options: Print placeholder message
        - Retour au menu: QuitToMenuEvent
        """
        event_bus = get_event_bus()

        if self.menu_items[self.selected_index] == "Reprendre":
            self.is_paused = False
            if self.hud_system:
                self.hud_system.hud.on_resume()
            event_bus.emit(ResumeGameEvent())
        elif self.menu_items[self.selected_index] == "Options":
            options_menu = OptionsMenu(option.current_resolution, option.flags)
            return_to_menu, new_res, new_flags = options_menu.run(self.screen)
            if return_to_menu:
                option.current_resolution = new_res
                option.flags = new_flags
                # Get current screen reference (may have been recreated)
                self.screen = pygame.display.get_surface()
                # Emit resize event to update all game systems if resolution changed
                from events.resize_event import ResizeEvent

                event_bus.emit(ResizeEvent(new_res))
                # Resume the game after closing options
                self.is_paused = False
                if self.hud_system:
                    self.hud_system.hud.on_resume()
        elif self.menu_items[self.selected_index] == "Retour au menu":
            self.is_paused = False
            event_bus.emit(QuitToMenuEvent())

    def process(self, dt: float):
        """Render the pause menu overlay and all UI elements.

        Args:
            dt: Delta time since last frame (unused, kept for Processor interface)
        """
        if not self.is_paused:
            return

        w, h = self.screen.get_size()

        # Semi-transparent overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        try:
            title_font = pygame.font.Font(Config.get_assets(key="font"), 48)
        except:
            title_font = pygame.font.Font(None, 64)

        title_surface = title_font.render("PAUSE", True, (255, 255, 255))
        title_x = w // 2 - title_surface.get_width() // 2
        title_y = h // 4 - 80

        shadow_surface = title_font.render("PAUSE", True, (60, 60, 60))
        self.screen.blit(shadow_surface, (title_x + 3, title_y + 3))
        self.screen.blit(title_surface, (title_x, title_y))

        # Buttons
        self.button_rects.clear()
        button_width = 450
        button_height = 50
        button_spacing = 70
        start_y = h // 2 + 20

        for i, item in enumerate(self.menu_items):
            y = start_y + i * button_spacing
            x = w // 2 - button_width // 2
            rect = pygame.Rect(x, y, button_width, button_height)
            self.button_rects.append(rect)
            is_hovered = i == self.selected_index
            self.draw_button(self.screen, rect, item, is_hovered)

        # Info text
        info_font = pygame.font.Font(Config.get_assets(key="font"), 12)
        info_text = info_font.render(
            "Presque pas Minecraft 1.16", True, (220, 220, 220)
        )
        self.screen.blit(info_text, (20, h - 20))
