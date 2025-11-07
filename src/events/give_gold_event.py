from core.ecs.event import Event


class GiveGoldEvent(Event):
    def __init__(self):
        super().__init__()
