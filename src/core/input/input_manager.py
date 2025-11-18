import pygame
import esper

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

        # Les touches qui seront utiles si on les presse
        self.key_bindings_press = {
            pygame.K_LCTRL: InputAction.SWITCH_TROOP,
            pygame.K_RCTRL: InputAction.SWITCH_TROOP,
            pygame.K_SPACE: InputAction.CAMERA_RESET,
            pygame.K_F3: InputAction.DEBUG_TOGGLE,
            pygame.K_g: InputAction.GIVE_GOLD,
            pygame.K_k: InputAction.SWITCH_CONTROL,
            pygame.K_ESCAPE: InputAction.PAUSE,
        }

        # Les touches qui seront utiles si on les release
        self.key_bindings_release = {}

        # Les touches qui seront utiles si on les maintient
        self.key_bindings_hold = {
            pygame.K_UP: InputAction.CAMERA_UP,
            pygame.K_DOWN: InputAction.CAMERA_DOWN,
            pygame.K_LEFT: InputAction.CAMERA_LEFT,
            pygame.K_RIGHT: InputAction.CAMERA_RIGHT,
        }

        self.mouse_bindings_press = {
            1: InputAction.START_SELECT,
            3: InputAction.MOVE_ORDER,
        }

        self.mouse_bindings_release = {1: InputAction.STOP_SELECT}

        self.mouse_bindings_hold = {1: InputAction.SELECT}

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
