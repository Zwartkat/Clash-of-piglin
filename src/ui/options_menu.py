"""Options menu system with tabbed interface for Display, Controls, and AI settings."""

import pygame
import json
import os
from typing import Dict, Tuple, List, Optional
from enum import Enum

from core.config import Config
from enums.input_actions import InputAction
from enums.entity.entity_type import EntityType


class OptionsTab(Enum):
    """Available tabs in the options menu."""

    DISPLAY = 0
    CONTROLS = 1
    AI = 2


class OptionsMenu:
    """
    Complete options menu with three tabs:
    - Display: Resolution, fullscreen, volume, vsync
    - Controls: Keybind configuration for all actions
    - AI: AI selection for each unit type per team
    """

    # Available AIs for each unit type
    AVAILABLE_AIS = {
        EntityType.BRUTE: ["ADMA"],
        EntityType.CROSSBOWMAN: ["SCPR", "LOVA"],
        EntityType.GHAST: ["MAPI", "JEVA"],
    }

    # Human-readable names for actions
    ACTION_NAMES = {
        InputAction.START_SELECT: "Commencer sélection",
        InputAction.STOP_SELECT: "Arrêter sélection",
        InputAction.SELECT: "Sélectionner",
        InputAction.MOVE_ORDER: "Ordre de mouvement",
        InputAction.SWITCH_TROOP: "Changer de troupe",
        InputAction.CAMERA_UP: "Caméra haut",
        InputAction.CAMERA_DOWN: "Caméra bas",
        InputAction.CAMERA_LEFT: "Caméra gauche",
        InputAction.CAMERA_RIGHT: "Caméra droite",
        InputAction.CAMERA_RESET: "Réinitialiser caméra",
        InputAction.ZOOM: "Zoom",
        InputAction.PAUSE: "Pause",
        InputAction.DEBUG_TOGGLE: "Debug",
        InputAction.GIVE_GOLD: "Donner or",
        InputAction.SWITCH_CONTROL: "Changer contrôle",
    }

    def __init__(self, initial_resolution: Tuple[int, int], initial_flags: int):
        """Initialize the options menu.

        Args:
            initial_resolution: Current screen resolution
            initial_flags: Current pygame display flags
        """
        self.current_tab = OptionsTab.DISPLAY
        self.tabs = ["Affichage", "Contrôles", "IA"]

        # Display settings
        self.current_resolution = initial_resolution
        self.flags = initial_flags
        self.fullscreen = bool(initial_flags & pygame.FULLSCREEN)
        self.borderless = False
        self.current_volume = 0.8
        self.vsync_enabled = True
        self.windowed_resolution = initial_resolution  # Store windowed resolution

        # Get native screen resolution for fullscreen
        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            self.native_resolution = tuple(desktop_sizes[0])
        else:
            info = pygame.display.Info()
            self.native_resolution = (info.current_w, info.current_h)

        # Initialize mixer if not already done
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass

        # Compute available resolutions
        self._init_resolutions()

        # Controls settings
        self.key_bindings = self._load_default_keybinds()
        self.waiting_for_key = None  # Action waiting for key rebind

        # AI settings
        self.ai_config = self._load_ai_config()

        # UI state
        self.selected_index = 0
        self.scroll_offset = 0
        self.dragging_volume = False

        # Load saved settings if they exist
        self._load_settings()

    def _init_resolutions(self):
        """Initialize available screen resolutions."""
        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            desktop = tuple(desktop_sizes[0])
        else:
            info = pygame.display.Info()
            desktop = (info.current_w, info.current_h)

        candidate_resolutions = [
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1366, 768),
            (1600, 900),
            (1920, 1080),
            desktop,
        ]

        seen = set()
        self.possible_resolutions = []
        for r in candidate_resolutions:
            if not isinstance(r, tuple):
                continue
            if r[0] <= desktop[0] and r[1] <= desktop[1]:
                if r not in seen:
                    seen.add(r)
                    self.possible_resolutions.append(r)
        self.possible_resolutions.sort(key=lambda x: (x[0], x[1]))

    def _load_default_keybinds(self) -> Dict:
        """Load default keybindings."""
        return {
            InputAction.SWITCH_TROOP: pygame.K_LCTRL,
            InputAction.CAMERA_RESET: pygame.K_SPACE,
            InputAction.DEBUG_TOGGLE: pygame.K_F3,
            InputAction.GIVE_GOLD: pygame.K_g,
            InputAction.SWITCH_CONTROL: pygame.K_k,
            InputAction.PAUSE: pygame.K_ESCAPE,
            InputAction.CAMERA_UP: pygame.K_UP,
            InputAction.CAMERA_DOWN: pygame.K_DOWN,
            InputAction.CAMERA_LEFT: pygame.K_LEFT,
            InputAction.CAMERA_RIGHT: pygame.K_RIGHT,
        }

    def _load_ai_config(self) -> Dict:
        """Load default AI configuration."""
        return {
            1: {  # Team 1
                EntityType.BRUTE: "ADMA",
                EntityType.CROSSBOWMAN: "SCPR",
                EntityType.GHAST: "MAPI",
            },
            2: {  # Team 2
                EntityType.BRUTE: "ADMA",
                EntityType.CROSSBOWMAN: "LOVA",
                EntityType.GHAST: "JEVA",
            },
        }

    def _load_settings(self):
        """Load settings from file if it exists."""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    data = json.load(f)

                    # Load display settings
                    if "display" in data:
                        self.current_volume = data["display"].get("volume", 0.8)
                        self.vsync_enabled = data["display"].get("vsync", True)
                        self.borderless = data["display"].get("borderless", False)
                        saved_res = data["display"].get("windowed_resolution")
                        if (
                            saved_res
                            and isinstance(saved_res, list)
                            and len(saved_res) == 2
                        ):
                            self.windowed_resolution = tuple(saved_res)

                    # Load keybinds (convert string keys back to InputAction enums)
                    if "keybinds" in data:
                        for action_name, key_code in data["keybinds"].items():
                            try:
                                action = InputAction[action_name]
                                self.key_bindings[action] = key_code
                            except (KeyError, ValueError):
                                pass

                    # Load AI config
                    if "ai" in data:
                        for team_str, units in data["ai"].items():
                            team = int(team_str)
                            for unit_str, ai_name in units.items():
                                try:
                                    unit_type = EntityType[unit_str]
                                    if ai_name in self.AVAILABLE_AIS.get(unit_type, []):
                                        self.ai_config[team][unit_type] = ai_name
                                except (KeyError, ValueError):
                                    pass
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save current settings to file."""
        try:
            data = {
                "display": {
                    "volume": self.current_volume,
                    "vsync": self.vsync_enabled,
                    "borderless": self.borderless,
                    "windowed_resolution": list(self.windowed_resolution),
                },
                "keybinds": {
                    action.name: key_code
                    for action, key_code in self.key_bindings.items()
                },
                "ai": {
                    str(team): {
                        unit_type.name: ai_name for unit_type, ai_name in units.items()
                    }
                    for team, units in self.ai_config.items()
                },
            }

            with open("settings.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def apply_ai_config(self):
        """Apply AI configuration to the game."""
        from config.ai_mapping import IA_MAP

        for team in [1, 2]:
            for unit_type in [
                EntityType.BRUTE,
                EntityType.CROSSBOWMAN,
                EntityType.GHAST,
            ]:
                if unit_type in self.ai_config[team]:
                    IA_MAP[unit_type][team] = self.ai_config[team][unit_type]

    def apply_keybinds(self):
        """Apply keybind configuration to the input manager."""
        # Just save to file, will be loaded on game start
        pass

    def _apply_keybinds_realtime(self):
        """Apply keybinds to currently running game."""
        try:
            import esper
            from core.input.input_manager import InputManager

            # Find the InputManager processor in esper
            for processor in esper._processors:
                if isinstance(processor, InputManager):
                    # Rebuild keybind dictionaries
                    processor.key_bindings_press = {}
                    processor.key_bindings_hold = {}

                    for action, key_code in self.key_bindings.items():
                        if action in [
                            InputAction.SWITCH_TROOP,
                            InputAction.CAMERA_RESET,
                            InputAction.DEBUG_TOGGLE,
                            InputAction.GIVE_GOLD,
                            InputAction.SWITCH_CONTROL,
                            InputAction.PAUSE,
                        ]:
                            processor.key_bindings_press[key_code] = action
                        elif action in [
                            InputAction.CAMERA_UP,
                            InputAction.CAMERA_DOWN,
                            InputAction.CAMERA_LEFT,
                            InputAction.CAMERA_RIGHT,
                        ]:
                            processor.key_bindings_hold[key_code] = action
                            if key_code not in processor.keys_down:
                                processor.keys_down[key_code] = False
                    break
        except Exception as e:
            print(f"Could not apply keybinds in real-time: {e}")
            pass

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events.        Args:
            event: Pygame event to process

        Returns:
            True if event was consumed, False to continue processing
        """
        if event.type == pygame.KEYDOWN:
            # If waiting for a key rebind
            if self.waiting_for_key is not None:
                if event.key != pygame.K_ESCAPE:  # ESC to cancel
                    self.key_bindings[self.waiting_for_key] = event.key
                    # Apply immediately if in game
                    self.save_settings()
                    self._apply_keybinds_realtime()
                self.waiting_for_key = None
                return True

            # Tab navigation
            if event.key == pygame.K_TAB:
                self.current_tab = OptionsTab(
                    (self.current_tab.value + 1) % len(OptionsTab)
                )
                self.selected_index = 0
                self.scroll_offset = 0
                return True

            # Navigation
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
                return True
            elif event.key == pygame.K_DOWN:
                max_index = self._get_max_index()
                self.selected_index = min(max_index, self.selected_index + 1)
                return True
            elif event.key == pygame.K_LEFT:
                self._handle_left()
                return True
            elif event.key == pygame.K_RIGHT:
                self._handle_right()
                return True
            elif event.key == pygame.K_RETURN:
                return self._handle_select()
            elif event.key == pygame.K_ESCAPE:
                return False  # Exit menu

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_mouse_click(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_volume = False

        elif event.type == pygame.MOUSEMOTION and self.dragging_volume:
            self._handle_volume_drag(event.pos)

        return True

    def _get_max_index(self) -> int:
        """Get maximum selectable index for current tab."""
        if self.current_tab == OptionsTab.DISPLAY:
            return 4  # Resolution, Fullscreen, Volume, Sound, Back
        elif self.current_tab == OptionsTab.CONTROLS:
            return len(self.key_bindings) + 1  # All keybinds + Reset + Back
        else:  # AI tab
            return 6  # 3 units per team + Back

    def _handle_left(self):
        """Handle left arrow key."""
        if self.current_tab == OptionsTab.DISPLAY:
            if self.selected_index == 2:  # Volume
                self.current_volume = max(0.0, self.current_volume - 0.05)
                try:
                    pygame.mixer.music.set_volume(self.current_volume)
                except Exception:
                    pass
        elif self.current_tab == OptionsTab.AI:
            self._cycle_ai(-1)

    def _handle_right(self):
        """Handle right arrow key."""
        if self.current_tab == OptionsTab.DISPLAY:
            if self.selected_index == 2:  # Volume
                self.current_volume = min(1.0, self.current_volume + 0.05)
                try:
                    pygame.mixer.music.set_volume(self.current_volume)
                except Exception:
                    pass
        elif self.current_tab == OptionsTab.AI:
            self._cycle_ai(1)

    def _handle_select(self) -> bool:
        """Handle Enter key selection.

        Returns:
            True to continue in menu, False to exit
        """
        if self.current_tab == OptionsTab.DISPLAY:
            if self.selected_index == 0:  # Resolution
                current_index = self.possible_resolutions.index(self.current_resolution)
                self.current_resolution = self.possible_resolutions[
                    (current_index + 1) % len(self.possible_resolutions)
                ]
                self.windowed_resolution = self.current_resolution
                # Apply immediately if not in fullscreen
                if not self.fullscreen:
                    self.flags = pygame.NOFRAME if self.borderless else 0
                    try:
                        pygame.display.set_mode(self.current_resolution, self.flags)
                    except Exception as e:
                        print(f"Failed to change resolution: {e}")
                return True
            elif self.selected_index == 1:  # Fullscreen
                # Toggle between windowed and fullscreen
                if not self.fullscreen and not self.borderless:
                    # Go to fullscreen
                    self.fullscreen = True
                    self.borderless = False
                    old_res = self.current_resolution
                    self.windowed_resolution = old_res
                    self.current_resolution = self.native_resolution
                    self.flags = pygame.FULLSCREEN
                elif self.fullscreen:
                    # Go back to windowed
                    self.fullscreen = False
                    self.current_resolution = self.windowed_resolution
                    self.flags = 0
                else:
                    # Currently borderless, go to fullscreen
                    self.fullscreen = True
                    self.borderless = False
                    self.current_resolution = self.native_resolution
                    self.flags = pygame.FULLSCREEN

                try:
                    pygame.display.set_mode(self.current_resolution, self.flags)
                except Exception as e:
                    print(f"Failed to toggle fullscreen: {e}")
                return True
            elif self.selected_index == 2:  # Borderless windowed
                # Toggle between windowed and borderless windowed
                if not self.fullscreen and not self.borderless:
                    # Go to borderless
                    self.borderless = True
                    self.flags = pygame.NOFRAME
                elif self.borderless:
                    # Go back to normal windowed
                    self.borderless = False
                    self.flags = 0
                else:
                    # Currently fullscreen, go to borderless
                    self.fullscreen = False
                    self.borderless = True
                    self.current_resolution = self.windowed_resolution
                    self.flags = pygame.NOFRAME

                try:
                    pygame.display.set_mode(self.current_resolution, self.flags)
                except Exception as e:
                    print(f"Failed to toggle borderless: {e}")
                return True
            elif self.selected_index == 3:  # Sound On/Off
                self.current_volume = 0.0 if self.current_volume > 0 else 0.5
                try:
                    pygame.mixer.music.set_volume(self.current_volume)
                except Exception:
                    pass
                return True
            elif self.selected_index == 4:  # Back
                return False

        elif self.current_tab == OptionsTab.CONTROLS:
            if self.selected_index < len(self.key_bindings):
                action = list(self.key_bindings.keys())[self.selected_index]
                self.waiting_for_key = action
                return True
            elif self.selected_index == len(self.key_bindings):  # Reset to defaults
                self.key_bindings = self._load_default_keybinds()
                return True
            else:  # Back
                return False

        elif self.current_tab == OptionsTab.AI:
            if self.selected_index < 6:
                self._cycle_ai(1)
                return True
            else:  # Back
                return False

        return True

    def _cycle_ai(self, direction: int):
        """Cycle through available AIs for selected unit/team."""
        if self.selected_index >= 6:
            return

        team = 1 if self.selected_index < 3 else 2
        unit_types = [EntityType.BRUTE, EntityType.CROSSBOWMAN, EntityType.GHAST]
        unit_type = unit_types[self.selected_index % 3]

        available = self.AVAILABLE_AIS[unit_type]
        current = self.ai_config[team][unit_type]

        try:
            current_index = available.index(current)
            new_index = (current_index + direction) % len(available)
            self.ai_config[team][unit_type] = available[new_index]
        except ValueError:
            self.ai_config[team][unit_type] = available[0]

    def _handle_mouse_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click events.

        Returns:
            True to continue in menu, False to exit
        """
        mx, my = pos

        # Check tab clicks
        tab_y = 90
        tab_width = 180
        tab_height = 40
        tab_spacing = 10
        w = pygame.display.get_surface().get_width()
        start_x = (
            w - (tab_width * len(self.tabs) + tab_spacing * (len(self.tabs) - 1))
        ) // 2

        for i in range(len(self.tabs)):
            tab_x = start_x + i * (tab_width + tab_spacing)
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            if tab_rect.collidepoint(pos):
                self.current_tab = OptionsTab(i)
                self.selected_index = 0
                self.scroll_offset = 0
                return True

        # Check content clicks (approximate based on rendered text positions)
        content_y = tab_y + tab_height + 30

        if self.current_tab == OptionsTab.DISPLAY:
            for i in range(
                5
            ):  # 5 options in display (Resolution, Fullscreen, Volume, Sound, Back)
                item_rect = pygame.Rect(50, content_y + i * 50, 600, 40)
                if item_rect.collidepoint(pos):
                    self.selected_index = i
                    return self._handle_select()

        elif self.current_tab == OptionsTab.CONTROLS:
            max_items = len(self.key_bindings) + 1  # +1 for back
            for i in range(max_items):
                item_rect = pygame.Rect(50, content_y + i * 45, 800, 40)
                if item_rect.collidepoint(pos):
                    self.selected_index = i
                    return self._handle_select()

        elif self.current_tab == OptionsTab.AI:
            # Team 1 items
            for i in range(3):
                item_rect = pygame.Rect(50, content_y + 40 + i * 45, 400, 40)
                if item_rect.collidepoint(pos):
                    self.selected_index = i
                    return True

            # Team 2 items
            team2_y = content_y + 180
            for i in range(3):
                item_rect = pygame.Rect(50, team2_y + 40 + i * 45, 400, 40)
                if item_rect.collidepoint(pos):
                    self.selected_index = i + 3
                    return True

            # Back button
            back_rect = pygame.Rect(50, team2_y + 180, 200, 40)
            if back_rect.collidepoint(pos):
                self.selected_index = 6
                return self._handle_select()

        return True

    def _handle_volume_drag(self, pos: Tuple[int, int]):
        """Handle volume slider dragging."""
        # Implementation depends on slider rect from render
        pass

    def render(self, screen: pygame.Surface):
        """Render the options menu.

        Args:
            screen: Surface to render on
        """
        w, h = screen.get_size()

        # Background
        screen.fill((30, 30, 30))

        # Title
        try:
            title_font = pygame.font.Font(Config.get_assets(key="font"), 48)
            font = pygame.font.Font(Config.get_assets(key="font"), 24)
            small_font = pygame.font.Font(Config.get_assets(key="font"), 18)
        except:
            title_font = pygame.font.Font(None, 64)
            font = pygame.font.Font(None, 32)
            small_font = pygame.font.Font(None, 24)

        title_surf = title_font.render("OPTIONS", True, (255, 255, 255))
        title_x = w // 2 - title_surf.get_width() // 2
        screen.blit(title_surf, (title_x, 20))

        # Tabs
        tab_y = 90
        tab_width = 180
        tab_height = 40
        tab_spacing = 10
        start_x = (
            w - (tab_width * len(self.tabs) + tab_spacing * (len(self.tabs) - 1))
        ) // 2

        for i, tab_name in enumerate(self.tabs):
            tab_x = start_x + i * (tab_width + tab_spacing)
            is_active = i == self.current_tab.value

            color = (80, 80, 80) if is_active else (50, 50, 50)
            border_color = (200, 200, 200) if is_active else (100, 100, 100)

            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            pygame.draw.rect(screen, color, tab_rect, border_radius=8)
            pygame.draw.rect(screen, border_color, tab_rect, 2, border_radius=8)

            tab_text = font.render(tab_name, True, (255, 255, 255))
            text_x = tab_x + (tab_width - tab_text.get_width()) // 2
            text_y = tab_y + (tab_height - tab_text.get_height()) // 2
            screen.blit(tab_text, (text_x, text_y))

        # Content area
        content_y = tab_y + tab_height + 30

        if self.current_tab == OptionsTab.DISPLAY:
            self._render_display_tab(screen, font, small_font, 50, content_y, w, h)
        elif self.current_tab == OptionsTab.CONTROLS:
            self._render_controls_tab(screen, font, small_font, 50, content_y, w, h)
        else:  # AI tab
            self._render_ai_tab(screen, font, small_font, 50, content_y, w, h)

    def _render_display_tab(self, screen, font, small_font, x, y, w, h):
        """Render Display settings tab."""
        options = [
            f"Résolution: {self.current_resolution[0]}x{self.current_resolution[1]}",
            f"Plein écran: {'Oui' if self.fullscreen else 'Non'}",
            f"Volume: {int(self.current_volume * 100)}%",
            f"Son: {'Oui' if self.current_volume > 0 else 'Non'}",
            "< Retour",
        ]

        for i, option in enumerate(options):
            color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)
            text_surf = font.render(option, True, color)
            screen.blit(text_surf, (x, y + i * 50))

            # Volume slider
            if i == 2 and self.selected_index == 2:
                slider_x = x + 250
                slider_y = y + i * 50 + 10
                slider_w = 300
                slider_h = 10

                # Track
                pygame.draw.rect(
                    screen,
                    (100, 100, 100),
                    (slider_x, slider_y, slider_w, slider_h),
                    border_radius=5,
                )

                # Filled portion
                filled_w = int(slider_w * self.current_volume)
                pygame.draw.rect(
                    screen,
                    (170, 170, 170),
                    (slider_x, slider_y, filled_w, slider_h),
                    border_radius=5,
                )

                # Handle
                handle_x = slider_x + filled_w - 7
                handle_rect = pygame.Rect(handle_x, slider_y - 8, 14, 26)
                pygame.draw.rect(screen, (240, 240, 240), handle_rect, border_radius=6)
                pygame.draw.rect(
                    screen, (120, 120, 120), handle_rect, 2, border_radius=6
                )

    def _render_controls_tab(self, screen, font, small_font, x, y, w, h):
        """Render Controls settings tab."""
        actions = list(self.key_bindings.items())

        # Title
        hint_text = "Appuyez sur Entrée pour rebind, ESC pour annuler"
        hint_surf = small_font.render(hint_text, True, (150, 150, 150))
        screen.blit(hint_surf, (x, y - 25))

        for i, (action, key_code) in enumerate(actions):
            if i < self.scroll_offset:
                continue
            if y + (i - self.scroll_offset) * 45 > h - 100:
                break

            action_name = self.ACTION_NAMES.get(action, action.name)

            # Waiting for key input
            if self.waiting_for_key == action:
                key_name = "< Appuyez sur une touche >"
                color = (255, 100, 100)
            else:
                key_name = pygame.key.name(key_code).upper()
                color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)

            action_surf = font.render(action_name, True, color)
            key_surf = font.render(f"→ {key_name}", True, color)

            screen.blit(action_surf, (x, y + (i - self.scroll_offset) * 45))
            screen.blit(key_surf, (x + 400, y + (i - self.scroll_offset) * 45))

        # Reset button
        reset_index = len(actions)
        if self.selected_index == reset_index:
            reset_color = (255, 100, 100)
        else:
            reset_color = (200, 150, 150)

        reset_surf = font.render("Réinitialiser par défaut", True, reset_color)
        screen.blit(reset_surf, (x, y + (reset_index - self.scroll_offset) * 45 + 20))

        # Back button
        back_index = len(actions) + 1
        if self.selected_index == back_index:
            back_color = (255, 255, 100)
        else:
            back_color = (200, 200, 200)

        back_surf = font.render("< Retour", True, back_color)
        screen.blit(back_surf, (x, y + (back_index - self.scroll_offset) * 45 + 20))

    def _render_ai_tab(self, screen, font, small_font, x, y, w, h):
        """Render AI settings tab."""
        # Team 1
        team1_title = font.render("Équipe 1 (Rouge)", True, (255, 100, 100))
        screen.blit(team1_title, (x, y))

        unit_types = [
            (EntityType.BRUTE, "Brute"),
            (EntityType.CROSSBOWMAN, "Arbalétrier"),
            (EntityType.GHAST, "Ghast"),
        ]

        for i, (unit_type, unit_name) in enumerate(unit_types):
            current_ai = self.ai_config[1][unit_type]
            color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)

            unit_surf = font.render(f"{unit_name}:", True, color)
            ai_surf = font.render(f"< {current_ai} >", True, color)

            screen.blit(unit_surf, (x + 30, y + 40 + i * 45))
            screen.blit(ai_surf, (x + 250, y + 40 + i * 45))

        # Team 2
        team2_y = y + 180
        team2_title = font.render("Équipe 2 (Bleue)", True, (100, 100, 255))
        screen.blit(team2_title, (x, team2_y))

        for i, (unit_type, unit_name) in enumerate(unit_types):
            current_ai = self.ai_config[2][unit_type]
            color = (255, 255, 100) if i + 3 == self.selected_index else (200, 200, 200)

            unit_surf = font.render(f"{unit_name}:", True, color)
            ai_surf = font.render(f"< {current_ai} >", True, color)

            screen.blit(unit_surf, (x + 30, team2_y + 40 + i * 45))
            screen.blit(ai_surf, (x + 250, team2_y + 40 + i * 45))

        # Back button
        back_y = team2_y + 180
        back_color = (255, 255, 100) if self.selected_index == 6 else (200, 200, 200)
        back_surf = font.render("< Retour", True, back_color)
        screen.blit(back_surf, (x, back_y))

    def run(self, initial_screen: pygame.Surface) -> Tuple[bool, Tuple[int, int], int]:
        """Run the options menu loop.

        Args:
            initial_screen: Initial pygame surface

        Returns:
            Tuple of (return_to_menu, resolution, flags)
        """
        clock = pygame.time.Clock()
        running = True

        while running:
            # Always get current screen in case it was recreated
            screen = pygame.display.get_surface()
            self.render(screen)
            pygame.display.flip()
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False, self.current_resolution, self.flags

                if not self.handle_event(event):
                    # Exit menu
                    running = False

        # Apply settings
        self.save_settings()
        self.apply_ai_config()
        self.apply_keybinds()

        # Update display flags
        if self.fullscreen:
            self.flags = pygame.FULLSCREEN
        else:
            self.flags = 0

        if self.vsync_enabled and not self.fullscreen:
            self.flags |= pygame.SCALED

        return True, self.current_resolution, self.flags
