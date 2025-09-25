from core.component import Component


class Money(Component):
    """Composant who represent the money of a player"""

    amount: int
    generation_speed: int

    def __init__(self, amount):
        self.amount = amount
        self.generation_speed = 0.133
