import esper
from core.event_bus import EventBus
from events.event_input import EventInput
from enums.input_actions import InputAction
from systems.pathfinding_system import PATHFINDING_SYSTEM_INSTANCE


class DebugEventHandler(esper.Processor):
    """
    Gère les événements liés au mode debug (F3).
    """

    def __init__(self, pathfinding_system):
        super().__init__()
        self.pathfinding_system = pathfinding_system
        # S'abonner aux événements DEBUG_TOGGLE
        EventBus.get_event_bus().subscribe(EventInput, self._on_input_event)

    def _on_input_event(self, event: EventInput):
        """Callback appelé quand un événement d'input est émis."""
        if event.action == InputAction.DEBUG_TOGGLE:
            # Basculer le mode debug du pathfinding
            if self.pathfinding_system:
                self.pathfinding_system.toggle_debug()
            else:
                print("ERREUR: pathfinding_system est None!")

    def process(self, dt):
        """Pas besoin de traitement dans la boucle principale."""
        pass
