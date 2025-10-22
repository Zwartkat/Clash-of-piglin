import math
import random

import esper
from components.ai import BaseAi
from components.ai_controller import AIController
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
from components.gameplay.attack import Attack
from components.gameplay.target import Target
from enums.entity.animation import Animation
from enums.entity.unit_type import UnitType


from ai.behavior_tree import Selector, Sequence, Condition, Action
from ai.behaviors.brute_actions import (
    ally_near,
    enemy_near,
    attack_target,
    wander,
    move_to_ally,
    protect_ally,
)


class BruteAI(BaseAi):
    def __init__(self):
        super().__init__()

        self.tree = Selector(
            # Sequence(Condition(enemy_near), Action(attack_target)),
            # Sequence(Condition(ally_near),Action(move_to_ally),Action(protect_ally)),
            Sequence(Action(wander)),
        )

    def decide(self, ent):
        self.tree.tick(ent)
