# src/systems/death_event_handler.py
import esper
from events.death_event import DeathEvent
from components.target import Target


class DeathEventHandler:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.event_bus.subscribe(DeathEvent, self.handle_death)

    def handle_death(self, death_event: DeathEvent):
        killer_team_id = death_event.player
        dead_entity_id = death_event.entity

        # delete the dead entity
        if esper.entity_exists(dead_entity_id):
            esper.delete_entity(dead_entity_id)

        # clear all Target components that reference the dead entity
        for ent, target in esper.get_component(Target):
            if target.target_entity_id == dead_entity_id:
                target.target_entity_id = None
