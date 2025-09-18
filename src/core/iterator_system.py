import esper
from esper import Processor
from abc import abstractmethod


class IteratingProcessor(Processor):
    def __init__(self, *components):
        super().__init__()
        self.components = components

    def process(self, dt):
        for ent, comps in esper.get_components(*self.components):
            print(ent)
            self.process_entity(ent, *comps, dt)

    @abstractmethod
    def process_entity(self, ent, *comps, dt):
        raise NotImplementedError
