from core.component import Component


class Attack(Component):
    """Composant who represent the ability to attack of an entity"""

    damage: int
    range: int
    attack_speed: float = 1.0
    last_attack: int = 0

    def __init__(self, damage: int, range: int, attack_speed: float, last_attack: int):
        self.damage = damage
        self.range = range
        self.attack_speed = attack_speed
        self.last_attack = last_attack
