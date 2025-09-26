from core.component import Component


class Squad(Component):
    """Composant who represent the squad of a player"""

    troops: int

    def __init__(self, troops: list):
        self.troops = troops
