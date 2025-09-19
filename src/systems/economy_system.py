import esper
from events.buy_event import BuyEvent
from events.sell_event import SellEvent


class EconomySystem(esper.Processor):
    def __init__(self, event_bus) -> None:
        self.event_bus = event_bus
        event_bus.subscribe(BuyEvent, self.buy)
        event_bus.subscribe(SellEvent, self.sell)

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

    def sell(self, event):
        player = event.player
        entity = event.entity
        player.money += entity.cost
        player.entities.remove(entity)
        print(
            f"Vous venez de vendre {entity} pour {entity.cost}, vous avez maintenant {player.money} pépites d'or"
        )
