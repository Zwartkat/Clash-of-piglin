from enum import Enum, auto


class InputAction(Enum):
    START_SELECT = auto()
    STOP_SELECT = auto()
    SELECT = auto()
    MOVE_ORDER = auto()
    SWITCH_TROOP = auto()
    CAMERA_UP = auto()
    CAMERA_DOWN = auto()
    CAMERA_LEFT = auto()
    CAMERA_RIGHT = auto()
    CAMERA_RESET = auto()
    ZOOM = auto()
    RESIZE = auto()
    QUIT = auto()
    SWITCH_CONTROL = auto()
    DEBUG_TOGGLE = auto()
    GIVE_GOLD = auto()
    PAUSE = auto()
    # Spawn units Team 1
    SPAWN_T1_CROSSBOWMAN = auto()
    SPAWN_T1_BRUTE = auto()
    SPAWN_T1_GHAST = auto()
    # Spawn units Team 2
    SPAWN_T2_CROSSBOWMAN = auto()
    SPAWN_T2_BRUTE = auto()
    SPAWN_T2_GHAST = auto()
