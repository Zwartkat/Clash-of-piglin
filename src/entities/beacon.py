from components.health import Health
from components.position import Position
from components.structure import Structure
from components.attack import Attack
from core.entity import Entity


class Beacon(Entity):

    def __init__(self):
        super().__init__(
            components=[
                Health(health=150),
                Position(x=0, y=0),
                Structure(),
                Attack(damage=0, range=3, attack_speed=0),
            ]
        )
