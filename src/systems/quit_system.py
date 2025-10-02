import esper
from events.event_input import EventInput
from enums.input_actions import InputAction


class QuitSystem(esper.Processor):
    def __init__(self, event_bus, game_state: dict):
        super().__init__()

        self.event_bus = event_bus
        self.game_state = game_state

        self.event_bus.subscribe(EventInput, self.on_input)

    def on_input(self, event: EventInput):
        if event.action == InputAction.QUIT:
            self.game_state["running"] = False

    def process(self, dt):
        pass
