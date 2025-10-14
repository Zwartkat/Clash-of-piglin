from enum import Enum, auto


class Status(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    RUNNING = auto()


class Node:
    def tick(self, ent: int):
        raise NotImplementedError()


class Sequence(Node):
    def __init__(self, *children):
        self.children = children

    def tick(self, ent: int):
        for child in self.children:
            status: Status = child.tick(ent)
            if status != Status.SUCCESS:
                return status
        return Status.SUCCESS


class Selector(Node):
    def __init__(self, *children):
        self.children = children

    def tick(self, ent: int):
        for child in self.children:
            status: Status = child.tick(ent)
            if status != Status.FAILURE:
                return status
        return Status.FAILURE


class Condition(Node):
    def __init__(self, func):
        self.func = func

    def tick(self, ent):
        return Status.SUCCESS if self.func(ent) else Status.FAILURE


class Action(Node):
    def __init__(self, func):
        self.func = func

    def tick(self, ent):
        return self.func(ent)
