from ai.ai_state import AiState
from components.ai import BaseAi

from core.accessors import get_config, get_debugger
from components.base.position import Position
from enums.config_key import ConfigKey
from enums.entity.animation import Animation


class AIController:
    """
    Composant qui relie une entité à son "cerveau" (IA).
    Il stocke les infos nécessaires pour la prise de décision.
    """

    def __init__(self, ent: int, brain=None):
        self.brain: BaseAi = brain
        self.state: AiState = AiState(ent)
