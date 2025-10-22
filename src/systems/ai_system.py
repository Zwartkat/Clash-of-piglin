from components.ai_controller import AIController
from core.ecs.iterator_system import IteratingProcessor


class AiSystem(IteratingProcessor):

    def __init__(self):
        super().__init__(AIController)

    def process_entity(self, ent, dt, ctrl: AIController):
        ctrl.state.update(dt)
        ctrl.brain.decide(ent)
