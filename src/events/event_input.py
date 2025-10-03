from enums.input_actions import InputAction


class EventInput:
    def __init__(self, action: InputAction, data=None):
        self.action = action
        self.data = data
