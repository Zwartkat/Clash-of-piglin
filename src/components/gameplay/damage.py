from core.ecs.component import Component


class Damage(Component):

    def __init__(self, timer: float = 2.0):
        self.timer: float = timer
