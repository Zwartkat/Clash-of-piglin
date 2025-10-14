from dataclasses import dataclass
from enum import Enum


class AIStateType(Enum):
    IDLE = 0
    ATTACKING = 1
    RETREATING = 2
    SUPPORTING = 3


@dataclass
class AIState:
    state: AIStateType = AIStateType.IDLE
    state_timer: float = 0.0  # seconds


@dataclass
class AIMemory:
    current_target_id: int = None
    last_known_target_pos: tuple = None


@dataclass
class PathRequest:
    destination: tuple = None
    path: list = None
    current_index: int = 0
