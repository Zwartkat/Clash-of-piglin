from core.ecs.component import Component


class Squad(Component):
    """Composant who represent the squad of a player"""

    troops: int

    def __init__(self, troops: list[int]):
        self.troops = troops
