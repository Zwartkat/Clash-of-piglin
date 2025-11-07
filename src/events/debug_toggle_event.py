from core.ecs.event import Event


class DebugToggleEvent(Event):
    """
    Event émis quand l'utilisateur appuie sur F3 pour toggle le mode debug.
    """

    def __init__(self):
        super().__init__()
