from ai.world_perception import WorldPerception
from components.ai_controller import AIController
from core.accessors import get_map
from core.ecs.iterator_system import IteratingProcessor
from enums.entity.entity_type import EntityType


class AiSystem(IteratingProcessor):

    def __init__(self):
        super().__init__(AIController)
        tile_size = len(get_map().tab)
        self.world_perception = WorldPerception(
            tile_size, {EntityType.BRUTE: 6 * tile_size}
        )

    def process_entity(self, ent, dt, ctrl: AIController):
        self.world_perception.update()
        ctrl.state.update(self.world_perception, dt)
        ctrl.brain.decide()
