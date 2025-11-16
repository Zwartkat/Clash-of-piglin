from core.ecs.component import Component


class Ai_flag(Component):

    def __init__(self) -> None:
        self.ai_controlled = True