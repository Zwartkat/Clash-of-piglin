from core.event import Event


class AttackEvent(Event):

    def __init__(self, fighter: int, target: int):
        self.fighter: int = fighter
        self.target: int = target
