from components.attack import Attack
from components.health import Health
from components.velocity import Velocity
from components.fly import Fly
from components.position import Position
from components.cost import Cost
from core.entity import Entity


class Ghast(Entity):

    def __init__(self):
        super().__init__(
            components=[
                Attack(damage=40, range=5, attack_speed=2.5),
                Health(health=70),
                Velocity(x=0, y=0, speed=10),
                Fly(),
                Position(x=0, y=0),
                Cost(value=820),
            ]
        )
        Attack(damage=40, range=5, attack_speed=2.5)
        Health(health=70)
        Velocity(x=0, y=0, speed=10)
        Fly()
        Position(x=0, y=0)
        Cost(value=820)
