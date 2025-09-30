import pygame
import esper

from enums.input_actions import InputAction
from enums.input_state import InputState
from events.event_input import EventInput


class InputManager(esper.Processor):
    def __init__(self, event_bus, camera):
        self.event_bus = event_bus
        self.camera = camera
        self.keys_down = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_RIGHT: False,
            pygame.K_LEFT: False,
        }

        self.key_bindings = {
            pygame.K_LCTRL: InputAction.SWITCH_TROOP,
            pygame.K_RCTRL: InputAction.SWITCH_TROOP,
            pygame.K_UP: InputAction.CAMERA_UP,
            pygame.K_DOWN: InputAction.CAMERA_DOWN,
            pygame.K_LEFT: InputAction.CAMERA_LEFT,
            pygame.K_RIGHT: InputAction.CAMERA_RIGHT,
            pygame.K_SPACE: InputAction.CAMERA_RESET,
        }

        self.mouse_bindings = {
            1: InputAction.SELECT,
            3: InputAction.MOVE_ORDER,
        }

    def process(self, dt):
        print("keys down:", self.keys_down)
        for event in pygame.event.get():
            self.handle_event(event)

        # Gestion des touches maintenues
        for key in self.keys_down.keys():
            self.event_bus.emit(EventInput(self.key_bindings[key], InputState.HELD))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            # Il faudra gérer ca différement je pense car ca quitte bien mais ca crée des erreurs quand même
            pygame.quit()

        elif event.type == pygame.KEYDOWN:
            if event.key in self.key_bindings:
                self.keys_down[event.key] = True
                self.event_bus.emit(
                    EventInput(self.key_bindings[event.key], InputState.PRESSED)
                )

        elif event.type == pygame.KEYUP:
            if event.key in self.key_bindings:
                self.keys_down[event.key] = False
                self.event_bus.emit(
                    EventInput(self.key_bindings[event.key], InputState.RELEASED)
                )

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in self.mouse_bindings:
                action = self.mouse_bindings[event.button]
                pos = self.camera.unapply(event.pos[0], event.pos[1])
                self.event_bus.emit(EventInput(action, InputState.PRESSED, pos))

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in self.mouse_bindings:
                action = self.mouse_bindings[event.button]
                pos = self.camera.unapply(event.pos[0], event.pos[1])
                self.event_bus.emit(EventInput(action, InputState.RELEASED, pos))

        elif event.type == pygame.MOUSEWHEEL:
            self.event_bus.emit(EventInput(InputAction.ZOOM, InputState.WHEEL, event.y))
