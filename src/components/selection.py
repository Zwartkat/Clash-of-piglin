from core.component import Component


class Selection(Component):
    def __init__(self, is_selected=False):
        self.is_selected = is_selected
