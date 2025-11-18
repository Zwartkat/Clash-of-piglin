import pygame
import random
from components.position import Position
from core.entity import Entity
from enums.entity_type import EntityType


class BruteAi:

    def __init__(self, entity, entity_list, map):
        self.entity: Entity = entity
        self.entity_list: list[Entity] = entity_list
        self.map = map

    def groupFriendlyEntities(self):
        list_entities_to_treat = [
            e
            for e in self.entity_list
            if e.team == self.entity.team and e != self.entity
        ]
        list_groups = []
        current_group = []

        while list_entities_to_treat != []:
            entity = list_entities_to_treat[
                random.randint(0, len(list_entities_to_treat))
            ]
            current_group.append(entity)
            list_units_to_search_neighbours = [entity]
            while list_entities_to_treat != []:
                entity_for_search = list_units_to_search_neighbours[
                    random.randint(0, len(list_units_to_search_neighbours))
                ]
                for entity in list_entities_to_treat:
                    entity_X = entity.get_component(Position).getX()
                    entity_Y = entity.get_component(Position).getY()
                    if (
                        entity.get_component(Position).getX()
                        <= entity_for_search.get_component(Position).getX()
                    ):
                        ...

    def process(self): ...
