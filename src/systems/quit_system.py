import esper
from events.quit_event import QuitEvent
from enums.input_actions import InputAction


class QuitSystem(esper.Processor):
    def __init__(self, event_bus, game_state: dict):
        super().__init__()

        self.event_bus = event_bus
        self.game_state = game_state

        self.event_bus.subscribe(QuitEvent, self.on_quit)

    def on_quit(self, event: QuitEvent):
        self.game_state["running"] = False

    def process(self, dt):
        pass
