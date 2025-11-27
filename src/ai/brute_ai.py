import pygame
import random
import esper
from components.position import Position
from core.entity import Entity
from enums.entity_type import EntityType
from ai.common_state_brute_ai import CommonState


class BruteAi:

    def __init__(self, common_state: CommonState, entity_id: int, map):
        self.common_state: CommonState = common_state
        self.entity_id = entity_id
        self.map = map
        self.group = None

    def add_to_group(self, group: int):
        self.common_state.groups[group].append(self.entity_id)
        self.group = group

    def count_in_group(group: list[int], entity_type: EntityType):
        return sum(
            1
            for ent in group
            if esper.component_for_entity(ent, EntityType) == entity_type
        )

    def process(self):
        group_members = self.common_state.groups.get(self.group, [])
        count_crossbow = self.count_in_group(group_members, EntityType.CROSSBOWMAN)
        count_brute = self.count_in_group(group_members, EntityType.BRUTE)

        if self.group == None or count_crossbow == 0:
            for group in self.common_state.groups:
                if self.count_in_group(
                    group, EntityType.CROSSBOWMAN
                ) > self.count_in_group(group, EntityType.BRUTE):
                    self.common_state.groups[group].append(self.entity_id)
