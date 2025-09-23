import esper
from core.component import Slowed, Blocked
from core.iterator_system import IteratingProcessor


class EffectSystem(IteratingProcessor):
    def __init__(self):
        super().__init__()

    def process(self, dt):
        self._process_timed_effects(dt)

    def _process_timed_effects(self, dt):
        for ent, slowed in esper.get_component(Slowed):
            if slowed.duration is not None:
                slowed.timer += dt
                if slowed.timer >= slowed.duration:
                    esper.remove_component(ent, Slowed)
