from components.attack import Attack
from components.health import Health
from components.position import Position
from components.velocity import Velocity
from components.cost import Cost
from core.entity import Entity


class Crossbowman(Entity):

    def __init__(self):
        super().__init__(
            components=[
                Attack(damage=20, range=3, attack_speed=2.0),
                Health(health=90),
                Velocity(x=0, y=0, speed=10),
                Position(x=0, y=0),
                Cost(value=425),
            ]
        )
