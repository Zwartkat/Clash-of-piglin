from components.attack import Attack
from components.health import Health
from components.position import Position
from components.velocity import Velocity
from components.cost import Cost
from core.entity import Entity


class Brute(Entity):

    def __init__(self):
        super().__init__(
            components=[
                Attack(damage=15, range=1, attack_speed=1.0),
                Health(health=100),
                Velocity(x=0, y=0, speed=20),
                Position(x=0, y=0),
                Cost(value=350),
            ]
        )
