import esper
from events.buy_event import BuyEvent
from events.death_event import DeathEvent
from components.cost import Cost
from components.money import Money
from core.iterator_system import IteratingProcessor


class EconomySystem(IteratingProcessor):
    def __init__(self, event_bus) -> None:
        super().__init__(Money)
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

    def process_entity(self, ent, dt: int, money):
        if dt < 60000:
            money.amount += 0.133
        elif dt < 120000:
            money.amount += 0.167
        elif dt < 180000:
            money.amount += 0.2
        elif dt < 240000:
            money.amount += 0.25
        else:
            money.amount += 0.3

        print(ent, ":", int(money.amount))
