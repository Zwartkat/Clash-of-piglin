from core.component import Component


class Attack(Component):
    """Composant who represent the ability to attack of an entity"""

    damage: int
    range: int
    attack_speed: float = 1.0

    def __init__(self, damage: int, range: int):
        self.damage = damage
        self.range = range