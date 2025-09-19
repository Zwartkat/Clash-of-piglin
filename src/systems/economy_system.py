import esper
from events.buy_event import BuyEvent
from components.cost import Cost


class EconomySystem(esper.Processor):
    def __init__(self, event_bus) -> None:
        self.event_bus = event_bus
        event_bus.subscribe(BuyEvent, self.buy)

    def buy(self, event):
        player = event.player
        entity = event.entity
        cost = esper.component_for_entity(entity, Cost)

        if player.money >= cost.value:
            player.money -= cost.value
            player.entities.append(entity)
            print(
                f"Vous avez acheté {entity} pour {cost.value}. Il vous reste: {player.money} pépites d'or"
            )
        else:
            print(f"Il vous manqua {cost.value - player.money} pour acheter {entity}")
