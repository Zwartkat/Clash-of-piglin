import esper
from esper import Processor
from abc import abstractmethod


class IteratingProcessor(Processor):
    def __init__(self, *components):
        super().__init__()
        self.components = components

    def process(self, dt):
        for ent, comps in esper.get_components(*self.components):
            self.process_entity(ent, dt, *comps)

    @abstractmethod
    def process_entity(self, ent, dt, *comps):
        raise NotImplementedError
