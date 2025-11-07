import copy
import esper
from typing import Type
from core.accessors import get_debugger
from core.ecs.component import Component
from core.ecs.iterator_system import IteratingProcessor


class EntityFactory:

    @staticmethod
    def create(*components: tuple[Component]) -> int:
        entity = esper.create_entity()
        for component in components:
            try:
                component = copy.deepcopy(component)
            except:
                get_debugger().error(
                    f"Failed to copy component {component} for unit {entity}"
                )
                components.append(component)
            esper.add_component(entity, component)
        return entity
