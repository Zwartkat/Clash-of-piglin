from core.component import Component


class Health(Component):
    """
    Composant who represent the health of an entity

    remaining : int : the remaining health of the entity
    full : int : the full health of the entity
    """

    remaining: int
    full: int

    def __init__(self, health: int):
        self.remaining = health
        self.full = health
