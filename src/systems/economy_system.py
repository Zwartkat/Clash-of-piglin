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

        if player.money >= cost.amount:
            player.money -= cost.amount
            player.entities.append(entity)
            print(
                f"Vous avez acheté {entity} pour {cost.amount}. Il vous reste: {player.money} pépites d'or"
            )
        else:
            print(f"Il vous manqua {cost.amount - player.money} pour acheter {entity}")

    def reward_money(self, event):
        player = event.player
        entity = event.entity
        entity_cost = esper.component_for_entity(entity, Cost)
        reward = int(entity_cost.amount / 10)  # 10% du prix de l'entité

        if (
            player.money + reward >= 1500
        ):  # cap de thunes (à définir quelque part peut etre un fichier de constante)
            player.money = 1500
        else:
            player.money += reward

        print(f"Vous avez tué {entity} et gagné {reward} pepites d'or")
