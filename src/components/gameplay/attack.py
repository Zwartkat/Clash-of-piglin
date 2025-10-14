from core.ecs.component import Component
from core.config import Config


class Attack(Component):
    """Composant who represent the ability to attack of an entity"""

    damage: int
    range: int
    attack_speed: float = 1.0
    last_attack: int = 0

    def __init__(
        self, damage: int, range: int, attack_speed: float, last_attack: int = 0
    ):
        self.damage = damage
        self.range = (range + 1) * Config.TILE_SIZE()
        self.attack_speed = attack_speed
        self.last_attack = last_attack
