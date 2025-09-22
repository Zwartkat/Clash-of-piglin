import esper
from components.attack import Attack
from components.target import Target
from components.position import Position
from core.iterator_system import IteratingProcessor


class CombatSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Attack, Target, Position)

    def process_entity(self, ent, dt, attack, target, pos) -> None:
        pass
