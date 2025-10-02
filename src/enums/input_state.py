from enum import Enum, auto


class InputState(Enum):
    PRESSED = auto()
    RELEASED = auto()
    HELD = auto()
    WHEEL = auto()
    RESIZE = auto()
