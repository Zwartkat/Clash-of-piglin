import esper
from events.buy_event import BuyEvent
from events.death_event import DeathEvent
from components.cost import Cost


class EconomySystem(esper.Processor):
    def __init__(self, event_bus) -> None:
        self.event_bus = event_bus
        event_bus.subscribe(BuyEvent, self.buy)
        event_bus.subscribe(DeathEvent, self.reward_money)

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

    def reward_money(self, event):
        player = event.player
        entity = event.entity
        reward = esper.component_for_entity(entity, Cost)

        player.money += int(reward.value / 10)  # 10% du prix de l'entité

        print(f"Vous avez tué {entity} et gagné {int(reward.value / 10)} pepites d'or")
