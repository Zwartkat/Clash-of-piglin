from components.case import Case
from core.game.camera import Camera
from core.config import Config
from core.ecs.event_bus import EventBus
from core.game.player_manager import PlayerManager


class Services:
    config: Config = None
    event_bus: EventBus = EventBus.get_event_bus()
    map: list[list[Case]] = None
    camera: Camera = None
    player_manager: PlayerManager = None
    start_time: int = 0
    finish_time: int = 0
