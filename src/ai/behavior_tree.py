from enum import Enum, auto

from ai.ai_state import AiState
from ai.brute import Action


class Status(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    RUNNING = auto()


class Node:
    def tick(self, ai_state: AiState):
        raise NotImplementedError()


class Sequence(Node):
    def __init__(self, *children):
        self.children = children

    def tick(self, ai_state: AiState):
        for child in self.children:
            status: Status = child.tick(ai_state)
            if status != Status.SUCCESS:
                return status
        return Status.SUCCESS


class Selector(Node):
    def __init__(self, *children):
        self.children = children

    def tick(self, ai_state: AiState):
        for child in self.children:
            status: Status = child.tick(ai_state)
            if status != Status.FAILURE:
                return status
        return Status.FAILURE


class ConditionNode(Node):

    def __init__(self, action: Action, threshold: float):
        self.action = action
        self.threshold = threshold

    def tick(self, ai_state: AiState) -> str:
        weight = ai_state.action_weights.get(self.action, 0.0)
        return Status.SUCCESS if weight >= self.threshold else Status.FAILURE


class ActionNode(Node):
    def __init__(self, action_class):
        self.action_class = action_class
        self.action_instance = None

    def tick(self, ai_state: AiState) -> Status:
        if not self.action_instance:
            self.action_instance = self.action_class(ai_state)

        result = self.action_instance.execute()
        return result
