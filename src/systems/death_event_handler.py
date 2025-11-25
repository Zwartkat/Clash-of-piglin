import esper
from core.accessors import get_audio_system
from components.gameplay.target import Target
from enums.entity.entity_type import EntityType
from events.death_event import DeathEvent
from enums.sounds import origin, reasons


class DeathEventHandler:
    """Handles cleanup when entities die in combat."""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.event_bus.subscribe(DeathEvent, self.handle_death)

    def handle_death(self, death_event: DeathEvent):
        """
        Clean up dead entity and clear all references to it.

        Args:
            death_event: Event with dead entity info and killer team
        """
        killer_team_id = death_event.player
        dead_entity_id = death_event.entity

        # Remove dead entity from game world
        if esper.entity_exists(dead_entity_id):
            esper.delete_entity(dead_entity_id)

        # Clear all targeting references to dead entity
        for ent, target in esper.get_component(Target):
            if target.target_entity_id == dead_entity_id:
                target.target_entity_id = None

        entity_type = esper.component_for_entity(dead_entity_id, EntityType)
        get_audio_system().play_sound(origin.ENTITY, entity_type, reasons.DEATH)
