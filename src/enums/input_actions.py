from enum import Enum, auto


class InputAction(Enum):
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
