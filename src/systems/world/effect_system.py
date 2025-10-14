import esper
from core.ecs.component import Slowed, Blocked
from core.ecs.iterator_system import IteratingProcessor


class EffectSystem(IteratingProcessor):
    """Manages timed effects like temporary buffs and debuffs."""

    def __init__(self):
        super().__init__()

    def process(self, dt):
        """
        Update all timed effects and remove expired ones.

        Args:
            dt: Time passed since last frame
        """
        self._process_timed_effects(dt)

    def _process_timed_effects(self, dt):
        """
        Update timers for temporary effects and remove when expired.

        Args:
            dt: Time to add to effect timers
        """
        for ent, slowed in esper.get_component(Slowed):
            if slowed.duration is not None:
                slowed.timer += dt
                if slowed.timer >= slowed.duration:
                    esper.remove_component(ent, Slowed)
