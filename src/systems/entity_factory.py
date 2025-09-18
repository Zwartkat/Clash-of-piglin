import esper
from typing import Type
from core.component import Component
from core.iterator_system import IteratingProcessor

class EntityFactory : 
        
    @staticmethod
    def create(*components : tuple[Component]) -> int:
        entity = esper.create_entity()
        for component in components:
            esper.add_component(entity, component)
        print(f"Entité créée : {entity}")
        return entity
    