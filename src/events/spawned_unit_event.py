class SpawnedUnitEvent:  # created to help tracking the id of newly spawned entities

    def __init__(self, entity_id: int):
        self.entity_id: int = entity_id
