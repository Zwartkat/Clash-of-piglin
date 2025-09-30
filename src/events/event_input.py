from enums.input_actions import InputAction
from enums.input_state import InputState


class EventInput:
    def __init__(self, action: InputAction, state: InputState, data=None):
        """
        state: "pressed", "released", "held", "wheel"
        data: Position souris ou direction / delta zoom / etc.
        """

        self.action = action
        self.state = state
        self.data = data
