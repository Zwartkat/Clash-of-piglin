import esper
import pygame
from core.game.camera import Camera
from core.ecs.event_bus import EventBus
from events.reset_cam_event import ResetCamEvent
from events.camera_zoom_event import CameraZoomEvent
from events.resize_event import ResizeEvent
from events.camera_up_event import CameraUpEvent
from events.camera_down_event import CameraDownEvent
from events.camera_left_event import CameraLeftEvent
from events.camera_right_event import CameraRightEvent


class CameraSystem(esper.Processor):
    def __init__(self, camera: Camera):
        super().__init__()

        self.camera = camera

        EventBus.get_event_bus().subscribe(ResetCamEvent, self.on_reset)
        EventBus.get_event_bus().subscribe(CameraZoomEvent, self.on_zoom)
        EventBus.get_event_bus().subscribe(ResizeEvent, self.on_resize)
        EventBus.get_event_bus().subscribe(CameraUpEvent, self.cam_up)
        EventBus.get_event_bus().subscribe(CameraDownEvent, self.cam_down)
        EventBus.get_event_bus().subscribe(CameraLeftEvent, self.cam_left)
        EventBus.get_event_bus().subscribe(CameraRightEvent, self.cam_right)

    def process(self, dt):
        pass

    def on_reset(self, event: ResetCamEvent):
        self.camera.set_position(0, 0)
        self.camera.set_zoom(1.0)

    def on_zoom(self, event: CameraZoomEvent):
        self.camera.zoom(0.05 * event.zoom)

    def on_resize(self, event: ResizeEvent):
        win_w, win_h = event.size[0], event.size[1]
        screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        # self.camera.set_size(win_w, win_h)

    def cam_up(self, event: CameraUpEvent):
        self.camera.move(0, -5)

    def cam_down(self, event: CameraDownEvent):
        self.camera.move(0, 5)

    def cam_right(self, event: CameraRightEvent):
        self.camera.move(5, 0)

    def cam_left(self, event: CameraLeftEvent):
        self.camera.move(-5, 0)
