from core.ecs.component import Component
from enums.entity.unit_type import UnitType


class Target(Component):
    def __init__(
        self, target_entity_id: int = None, allow_targets: list[UnitType] = None
    ):
        self.allow_targets: list[UnitType] = allow_targets
        self.target_entity_id = target_entity_id
