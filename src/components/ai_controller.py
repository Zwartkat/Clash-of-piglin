from components.ai import BaseAi
from components.base.position import Position
from enums.entity.animation import Animation


class AIController:
    """
    Composant qui relie une entité à son "cerveau" (IA).
    Il stocke les infos nécessaires pour la prise de décision.
    """

    def __init__(self, brain=None):
        self.path: list[Position] = []
        self.brain: BaseAi = brain
        self.state: Animation = Animation.IDLE
        self.target: int = None
        self.target_pos: Position = None
