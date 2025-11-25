from ai.ai_state import AiState
from ai.brute import BruteAI
from ai.ghast import JeromeGhast
from components.ai import BaseAi

from core.accessors import get_config, get_debugger
from components.base.position import Position
from enums.config_key import ConfigKey
from enums.entity.animation import Animation
from enums.entity.entity_type import EntityType


class AIController:
    """
    Composant qui relie une entité à son "cerveau" (IA).
    Il stocke les infos nécessaires pour la prise de décision.
    """

    def __init__(self, ent: int, state: AiState = None, brain: BaseAi = None):
        self.state = state
        self.brain = brain
