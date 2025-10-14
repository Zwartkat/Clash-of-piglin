from abc import abstractmethod

from core.ecs.component import Component


class BaseAi(Component):
    def __init__(self):
        pass

    @abstractmethod
    def decide():
        raise NotImplementedError()
