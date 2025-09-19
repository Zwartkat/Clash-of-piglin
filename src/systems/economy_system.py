import esper
from events.buy_event import BuyEvent


class EconomySystem(esper.Processor):
    def __init__(self, event_bus) -> None:
        self.event_bus = event_bus
        event_bus.subscribe(BuyEvent, self.buy)

    def buy(self, event):
        player = event.player
        entity = event.entity
        if player.money >= entity.cost:
            player.money -= entity.cost
            player.entities.append(entity)
            print(
                f"Vous avez acheté {entity} pour {entity.cost}. Il vous reste: {player.money} pépites d'or"
            )
        else:
            print(f"Il vous manqua {entity.cost - player.money} pour acheter {entity}")
