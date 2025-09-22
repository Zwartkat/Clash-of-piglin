import esper
from components.health import Health
from components.structure import Structure
from systems.entity_factory import EntityFactory
from event_bus import EventBus
from events.buy_event import BuyEvent


class Player(object):
    def __init__(self, event_bus) -> None:
        self.player_entities = []
        self.money = 600
        self.bastion = EntityFactory.create(
            Health(1000), Structure()
        )  # liste des composants du bastion
        self.event_bus = event_bus

    def buy_entity(self, list_components: list):
        entity = EntityFactory.create(list_components)
        self.player_entities.append(entity)
        self.event_bus.emit(BuyEvent(self, entity))
