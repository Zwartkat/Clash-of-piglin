from core.component import Component


class Cost(Component):
    """Composant who represent the cost of an entity"""

    amount: int

    def __init__(self, amount):
        self.amount = amount
