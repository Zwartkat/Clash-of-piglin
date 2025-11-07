from core.game.camera import Camera
from core.config import Config
from core.ecs.event_bus import EventBus
from core.game.player_manager import PlayerManager


class Services:
    start_time: int = 0
    finish_time: int = 0
