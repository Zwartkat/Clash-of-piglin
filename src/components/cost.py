from core.component import Component


class Cost(Component):
    """Composant who represent the cost of an entity"""

    value: int

    def __init__(self, value):
        self.value = value
