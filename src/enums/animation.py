from enum import Enum, auto


class Animation(Enum):
    IDLE = auto()
    WALK = auto()
    RUN = auto()
    ATTACK = auto()
    NONE = auto()
