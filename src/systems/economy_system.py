import esper
import pygame
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

        self.creation_time = pygame.time.get_ticks()

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

    def process_entity(self, ent, dt, money):

        time_elapsed = pygame.time.get_ticks() - self.creation_time

        # Changement de la vitesse de génération en fonction du temps
        if time_elapsed < 120000:
            money.generation_speed = 0.167
        elif time_elapsed < 180000:
            money.generation_speed = 0.2
        elif time_elapsed < 240000:
            money.generation_speed = 0.25
        else:
            money.generation_speed = 0.3

        # Ajout de l'argent au compte
        money.amount += money.generation_speed

        print("entité n°", ent, ":", int(money.amount))
        print("time elapsed:", time_elapsed)
