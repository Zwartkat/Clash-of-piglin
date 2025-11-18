import pygame
from ai.brute_ai import BruteAi
from enums.entity_type import EntityType


class AiSystem:
    """Système gérant les IA des entités."""

    def __init__(self):
        self.entity_list = []

    def process_entities(self):
        for entity in self.entity_list:
            ...
