import esper
from ai.ai_state import Action, AiState
from components.ai import BaseAi

from ai.behavior_tree import Selector, Sequence, ConditionNode, ActionNode
from ai.behaviors.brute_actions import (
    AttackAction,
    DefendBaseAction,
    ProtectAction,
    RetreatAction,
    TargetObjective,
    WanderAction,
)
from components.gameplay.selection import Selection


class BruteAI(BaseAi):
    def __init__(self, ai_state: AiState):
        super().__init__()
        self.ai_state = ai_state
        self.tree = Selector(
            Sequence(
                ConditionNode(Action.DEFEND_BASE, 1), ActionNode(DefendBaseAction)
            ),
            Sequence(ConditionNode(Action.PROTECT, 1), ActionNode(ProtectAction)),
            Sequence(ConditionNode(Action.RETREAT, 0.6), ActionNode(RetreatAction)),
            Sequence(ConditionNode(Action.ATTACK, 0.5), ActionNode(AttackAction)),
            Sequence(ConditionNode(Action.GOAL, 0), ActionNode(TargetObjective)),
            # Must be unused
            Sequence(ActionNode(WanderAction)),
        )

    def decide(self):
        """
        Call behavior tree to select an action to do if entity isn't select else it does nothing
        """
        ent: int = self.ai_state.entity
        if not esper.component_for_entity(ent, Selection).is_selected:
            self.tree.tick(self.ai_state)
