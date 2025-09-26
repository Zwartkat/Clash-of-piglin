from enum import Enum, auto


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    NONE = auto()


class Animation(Enum):
    IDLE = auto()
    WALK = auto()
    RUN = auto()
    ATTACK = auto()
    NONE = auto()


class Orientation(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()


class CaseType(Enum):
    NETHERRACK = auto()
    BLUE_NETHERRACK = auto()
    RED_NETHERRACK = auto()
    SOULSAND = auto()
    LAVA = auto()
