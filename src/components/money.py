from core.component import Component


class Money(Component):
    """Composant who represent the money of a player"""

    amount: int

    def __init__(self, amount):
        self.amount = amount
