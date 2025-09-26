import esper
import pygame
from events.buy_event import BuyEvent
from events.death_event import DeathEvent
from components.cost import Cost
from components.money import Money
from components.squad import Squad
from core.iterator_system import IteratingProcessor


class EconomySystem(esper.Processor):
    def __init__(self, event_bus) -> None:
        super().__init__()
        self.event_bus = event_bus
        event_bus.subscribe(BuyEvent, self.buy)
        event_bus.subscribe(DeathEvent, self.reward_money)

        self.creation_time = pygame.time.get_ticks()
        self.generation_speed = 0.133  # Valeur de base pour 0-1 minute

    def buy(self, event):
        player = event.player
        entity = event.entity
        cost = esper.component_for_entity(entity, Cost)
        money = esper.component_for_entity(player, Money)
        squad = esper.component_for_entity(player, Squad)

        if money.amount >= cost.amount:
            money.amount -= cost.amount
            squad.troops.append(entity)
            print(
                f"Vous avez acheté {entity} pour {cost.amount}. Il vous reste: {money.amount} pépites d'or"
            )
        else:
            print(f"Il vous manqua {cost.amount - money.amount} pour acheter {entity}")

    def reward_money(self, event):
        player = event.player
        entity = event.entity
        entity_cost = esper.component_for_entity(entity, Cost)
        money = esper.component_for_entity(player, Money)
        reward = int(entity_cost.amount / 10)  # 10% du prix de l'entité

        if (
            money.amount + reward >= 1500
        ):  # cap de thunes (à définir quelque part peut etre un fichier de constantes)
            money.amount = 1500
        else:
            money.amount += reward

        print(f"Vous avez tué {entity} et gagné {reward} pepites d'or")

    def process(self, dt):

        # Récupération du temps écoulé
        time_elapsed = pygame.time.get_ticks() - self.creation_time

        # Changement de la vitesse de génération en fonction du temps
        if 60000 < time_elapsed < 120000:
            self.generation_speed = 0.167
        elif 120000 < time_elapsed < 180000:
            self.generation_speed = 0.2
        elif 180000 < time_elapsed < 240000:
            self.generation_speed = 0.25
        elif time_elapsed > 240000:
            self.generation_speed = 0.3

        # Ajout de la thune aux comptes des joueurs
        for ent, money in esper.get_component(Money):
            if money.amount + self.generation_speed >= 1500:  # Cap
                money.amount = 1500
            else:
                money.amount += self.generation_speed
