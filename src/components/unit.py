from dataclasses import dataclass

from core.component import Component

from enums.entity_type import EntityType
from enums.unit_type import UnitType


@dataclass
class Unit(Component):
    entity_type: EntityType
    unit_type: UnitType
