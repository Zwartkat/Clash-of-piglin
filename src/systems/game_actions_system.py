import esper
import pygame
from events.event_input import EventInput
from core.event_bus import EventBus
from events.event_move import EventMoveTo
from systems.player_manager import PlayerManager
from systems.selection_system import SelectionSystem
from enums.input_actions import InputAction
from enums.input_state import InputState


class GameActionSystem(esper.Processor):
    def __init__(
        self,
        event_bus: EventBus,
        world,
        player_manager: PlayerManager,
        selection_system: SelectionSystem,
        camera,
    ):
        super().__init__()

        self.event_bus = event_bus
        self.world = world
        self.player_manager = player_manager
        self.selection_system = selection_system
        self.camera = camera

        self.event_bus.subscribe(EventInput, self.handle_events)

        self.action_bindings = {
            InputAction.SWITCH_TROOP: self.switch_troops,
            InputAction.CAMERA_RESET: self.reset_cam,
            InputAction.ZOOM: self.cam_zoom,
            InputAction.SELECT: self.select,
            InputAction.MOVE_ORDER: self.move_order,
            InputAction.CAMERA_UP: self.camera_up,
            InputAction.CAMERA_DOWN: self.camera_up,
            InputAction.CAMERA_RIGHT: self.camera_right,
            InputAction.CAMERA_LEFT: self.camera_left,
            InputAction.QUIT: self.quit_game,
        }

    def handle_events(self, event: EventInput):
        self.action_bindings[event.action](event)

    def switch_troops(self, event: EventInput):
        if event.state == InputState.PRESSED:
            self.player_manager.switch_player()
            self.selection_system.clear_selection(self.world)

    def reset_cam(self, event: EventInput):
        if event.state == InputState.PRESSED:
            self.camera.set_position(0, 0)
            self.camera.set_zoom(1.0)

    def cam_zoom(self, event: EventInput):
        self.camera.zoom(0.05 * event.data)

    def select(self, event: EventInput):
        if event.state == InputState.PRESSED:
            self.selection_system.handle_mouse_down(event.data, self.world)
        elif event.state == InputState.RELEASED:
            self.selection_system.handle_mouse_up(event.data, self.world)
        elif event.state == InputState.HELD:
            self.selection_system.handle_mouse_motion(event.data, self.world)

    def move_order(self, event: EventInput):
        if event.state == InputState.PRESSED:
            selected_entities = self.selection_system.get_selected_entities(self.world)

            if selected_entities:
                x, y = event.data
                from systems.troop_system import (
                    FormationSystem,
                    TROOP_GRID,
                    TROOP_CIRCLE,
                )

                positions = FormationSystem.calculate_formation_positions(
                    selected_entities,
                    x,
                    y,
                    spacing=35,
                    formation_type=TROOP_GRID,  # you can change to TROOP_CIRCLE if needed
                )

                for i, ent in enumerate(selected_entities):
                    if i < len(positions):
                        target_x, target_y = positions[i]
                        self.event_bus.emit(EventMoveTo(ent, target_x, target_y))

    def camera_up(self, event: EventInput):
        self.camera.move(0, -5)

    def camera_down(self, event: EventInput):
        self.camera.move(0, 5)

    def camera_right(self, event: EventInput):
        self.camera.move(5, 0)

    def camera_left(self, event: EventInput):
        self.camera.move(-5, 0)

    def quit_game(self, event: EventInput):
        pygame.quit()

    def process(self, dt):
        pass
