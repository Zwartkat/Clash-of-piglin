from core.component import Component


class UnitType(Component):
    def __init__(self, unit_type, name):
        self.unit_type = unit_type
        self.name = name
