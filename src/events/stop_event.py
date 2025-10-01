from core.event import Event


class StopEvent(Event):
    def __init__(self, entity: int):
        super().__init__()
        self.entity: int = entity

    def info(self):
        return super().info()
