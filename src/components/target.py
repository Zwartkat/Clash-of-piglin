from core.component import Component


class Target(Component):
    def __init__(self, target_entity_id: int = None):
        self.target_entity_id = target_entity_id
