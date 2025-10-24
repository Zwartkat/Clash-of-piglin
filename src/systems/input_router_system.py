import esper
import pygame
from core.services import Services
from events.event_input import EventInput
from events.quit_event import QuitEvent
from events.switch_event import SwitchEvent
from events.reset_cam_event import ResetCamEvent
from events.camera_zoom_event import CameraZoomEvent
from events.start_select_event import StartSelectEvent
from events.stop_select_event import StopSelectEvent
from events.move_order_event import MoveOrderEvent
from events.select_event import SelectEvent
from events.resize_event import ResizeEvent
from events.camera_up_event import CameraUpEvent
from events.camera_down_event import CameraDownEvent
from events.camera_left_event import CameraLeftEvent
from events.camera_right_event import CameraRightEvent
from events.debug_toggle_event import DebugToggleEvent
from core.event_bus import EventBus
from events.event_move import EventMoveTo
from enums.input_actions import InputAction
from core.camera import CAMERA


class InputRouterSystem(esper.Processor):
    def __init__(self):
        super().__init__()

        EventBus.get_event_bus().subscribe(EventInput, self.handle_events)

        # /!\ Attention, si l'action demande une data, mettre la classe de l'event, sinon, mettre un instance de l'event
        self.action_bindings = {
            InputAction.SWITCH_TROOP: SwitchEvent(),
            InputAction.CAMERA_RESET: ResetCamEvent(),
            InputAction.ZOOM: CameraZoomEvent,
            InputAction.START_SELECT: StartSelectEvent,
            InputAction.STOP_SELECT: StopSelectEvent,
            InputAction.SELECT: SelectEvent,
            InputAction.MOVE_ORDER: MoveOrderEvent,
            InputAction.CAMERA_UP: CameraUpEvent(),
            InputAction.CAMERA_DOWN: CameraDownEvent(),
            InputAction.CAMERA_RIGHT: CameraRightEvent(),
            InputAction.CAMERA_LEFT: CameraLeftEvent(),
            InputAction.QUIT: QuitEvent(),
            InputAction.RESIZE: ResizeEvent,
            InputAction.DEBUG_TOGGLE: DebugToggleEvent(),
        }

    def handle_events(self, event: EventInput):
        if event.data:
            EventBus.get_event_bus().emit(
                self.action_bindings[event.action](event.data)
            )
        else:
            EventBus.get_event_bus().emit(self.action_bindings[event.action])

    def process(self, dt):
        pass
