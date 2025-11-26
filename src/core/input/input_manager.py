import pygame
import esper
import json
import os

from core.accessors import get_event_bus
from core.game.camera import CAMERA
from core.ecs.event_bus import EventBus
from enums.input_actions import InputAction
from events.event_input import EventInput


class InputManager(esper.Processor):
    def __init__(self):

        self.keys_down = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_RIGHT: False,
            pygame.K_LEFT: False,
        }

        self.mouse_down = {1: False}

        # Keys useful when pressed
        self.key_bindings_press = self._load_keybinds_press()

        # Keys useful when released
        self.key_bindings_release = {}

        # Keys useful when held down
        self.key_bindings_hold = self._load_keybinds_hold()

        self.mouse_bindings_press = {
            1: InputAction.START_SELECT,
            3: InputAction.MOVE_ORDER,
        }

        self.mouse_bindings_release = {1: InputAction.STOP_SELECT}

        self.mouse_bindings_hold = {1: InputAction.SELECT}

    def _load_keybinds_press(self):
        """Load press keybinds from settings file or use defaults."""
        defaults = {
            pygame.K_LCTRL: InputAction.SWITCH_TROOP,
            pygame.K_RCTRL: InputAction.SWITCH_TROOP,
            pygame.K_SPACE: InputAction.CAMERA_RESET,
            pygame.K_F3: InputAction.DEBUG_TOGGLE,  # Debug only, not in options menu
            pygame.K_g: InputAction.GIVE_GOLD,  # Debug only, not in options menu
            pygame.K_ESCAPE: InputAction.PAUSE,
            pygame.K_1: InputAction.SPAWN_T1_CROSSBOWMAN,
            pygame.K_2: InputAction.SPAWN_T1_BRUTE,
            pygame.K_3: InputAction.SPAWN_T1_GHAST,
            pygame.K_7: InputAction.SPAWN_T2_CROSSBOWMAN,
            pygame.K_8: InputAction.SPAWN_T2_BRUTE,
            pygame.K_9: InputAction.SPAWN_T2_GHAST,
        }

        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    data = json.load(f)
                    if "keybinds" in data:
                        loaded = {}
                        # Keep debug keys in defaults
                        loaded[pygame.K_F3] = InputAction.DEBUG_TOGGLE
                        loaded[pygame.K_g] = InputAction.GIVE_GOLD

                        for action_name, key_code in data["keybinds"].items():
                            try:
                                action = InputAction[action_name]
                                # Only load press keybinds (not hold ones, not debug ones)
                                if action in [
                                    InputAction.SWITCH_TROOP,
                                    InputAction.CAMERA_RESET,
                                    InputAction.PAUSE,
                                    InputAction.SPAWN_T1_CROSSBOWMAN,
                                    InputAction.SPAWN_T1_BRUTE,
                                    InputAction.SPAWN_T1_GHAST,
                                    InputAction.SPAWN_T2_CROSSBOWMAN,
                                    InputAction.SPAWN_T2_BRUTE,
                                    InputAction.SPAWN_T2_GHAST,
                                ]:
                                    loaded[key_code] = action
                            except (KeyError, ValueError):
                                pass
                        if loaded:
                            return loaded
        except Exception as e:
            print(f"Error loading keybinds: {e}")

        return defaults

    def _load_keybinds_hold(self):
        """Load hold keybinds from settings file or use defaults."""
        defaults = {
            pygame.K_UP: InputAction.CAMERA_UP,
            pygame.K_DOWN: InputAction.CAMERA_DOWN,
            pygame.K_LEFT: InputAction.CAMERA_LEFT,
            pygame.K_RIGHT: InputAction.CAMERA_RIGHT,
        }

        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    data = json.load(f)
                    if "keybinds" in data:
                        loaded = {}
                        for action_name, key_code in data["keybinds"].items():
                            try:
                                action = InputAction[action_name]
                                # Only load hold keybinds
                                if action in [
                                    InputAction.CAMERA_UP,
                                    InputAction.CAMERA_DOWN,
                                    InputAction.CAMERA_LEFT,
                                    InputAction.CAMERA_RIGHT,
                                ]:
                                    loaded[key_code] = action
                                    # Update keys_down tracking
                                    if key_code not in self.keys_down:
                                        self.keys_down[key_code] = False
                            except (KeyError, ValueError):
                                pass
                        if loaded:
                            return loaded
        except Exception as e:
            print(f"Error loading keybinds: {e}")

        return defaults

    def process(self, dt):
        # for event in pygame.event.get():
        #     self.handle_event(event)

        # Gestion des touches maintenues
        for key, value in self.keys_down.items():
            if value:
                get_event_bus().emit(EventInput(self.key_bindings_hold[key]))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            get_event_bus().emit(EventInput(InputAction.QUIT))

        elif event.type == pygame.KEYDOWN:
            if event.key in self.keys_down:
                if event.key in self.key_bindings_press:
                    get_event_bus().emit(EventInput(self.key_bindings_press[event.key]))

                self.keys_down[event.key] = True

            elif event.key in self.key_bindings_press:
                get_event_bus().emit(EventInput(self.key_bindings_press[event.key]))

        elif event.type == pygame.KEYUP:
            if event.key in self.keys_down:
                if event.key in self.key_bindings_release:
                    get_event_bus().emit(
                        EventInput(self.key_bindings_release[event.key])
                    )
                self.keys_down[event.key] = False

            elif event.key in self.key_bindings_release:
                get_event_bus().emit(EventInput(self.key_bindings_release[event.key]))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in self.mouse_down:
                self.mouse_down[event.button] = True

            if event.button in self.mouse_bindings_press:
                action = self.mouse_bindings_press[event.button]
                pos = CAMERA.unapply(event.pos[0], event.pos[1])
                get_event_bus().emit(EventInput(action, pos))

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in self.mouse_down:
                self.mouse_down[event.button] = False

            if event.button in self.mouse_bindings_release:
                action = self.mouse_bindings_release[event.button]
                pos = CAMERA.unapply(event.pos[0], event.pos[1])
                get_event_bus().emit(EventInput(action, pos))

        elif event.type == pygame.MOUSEMOTION:
            for key, value in self.mouse_down.items():
                if value:
                    pos = CAMERA.unapply(event.pos[0], event.pos[1])
                    get_event_bus().emit(EventInput(self.mouse_bindings_hold[key], pos))

        elif event.type == pygame.MOUSEWHEEL:
            get_event_bus().emit(EventInput(InputAction.ZOOM, event.y))

        elif event.type == pygame.VIDEORESIZE:
            get_event_bus().emit(EventInput(InputAction.RESIZE, (event.w, event.h)))
