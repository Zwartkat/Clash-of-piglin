from __future__ import annotations
from typing import TYPE_CHECKING, cast
from core.ecs.entity import Entity
from enums.data_bus_key import DataBusKey
from enums.entity.entity_type import EntityType
from .data_bus import DATA_BUS

if TYPE_CHECKING:
    from core.config import Config
    from core.debugger import Debugger
    from core.ecs.event_bus import EventBus
    from core.game.camera import Camera
    from core.game.map import Map
    from systems.world.player_move_system import PlayerMoveSystem
    from systems.audio_system import AudioSystem

    from core.game.player_manager import PlayerManager


def get_config() -> "Config":
    instance = DATA_BUS.get(DataBusKey.CONFIG)
    if instance is None:
        get_debugger().error("Config not found in DATA_BUS")
    return cast("Config", instance)


def get_debugger() -> "Debugger":
    instance = DATA_BUS.get(DataBusKey.DEBUGGER)
    return cast("Debugger", instance)


def get_event_bus() -> "EventBus":
    instance = DATA_BUS.get(DataBusKey.EVENT_BUS)
    return cast("EventBus", instance)


def get_audio_system() -> AudioSystem:
    instance = DATA_BUS.get(DataBusKey.AUDIO_SYSTEM)
    return cast("AudioSystem", instance)


def get_camera() -> "Camera":
    instance = DATA_BUS.get(DataBusKey.CAMERA)
    return cast("Camera", instance)


def get_player_manager() -> "PlayerManager":
    instance = DATA_BUS.get(DataBusKey.PLAYER_MANAGER)
    return cast("PlayerManager", instance)


def get_entity(entity_type: EntityType) -> Entity:
    from config.units import UNITS

    return UNITS[entity_type]


def get_player_move_system() -> "PlayerMoveSystem":
    instance = DATA_BUS.get(DataBusKey.PLAYER_MOVEMENT_SYSTEM)
    return cast("PlayerMoveSystem", instance)


def get_map() -> "Map":
    instance = DATA_BUS.get(DataBusKey.MAP)
    return cast("Map", instance)
