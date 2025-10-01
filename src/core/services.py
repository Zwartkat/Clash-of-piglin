from core.camera import Camera
from core.config import Config
from core.event_bus import EventBus
from systems.player_manager import PlayerManager


class Services:
    config: Config = None
    event_bus: EventBus = None
    camera: Camera = None
    player_manager: PlayerManager = None
