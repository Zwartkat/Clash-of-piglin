import esper
import pygame
from components.base.team import Team
from core.accessors import get_debugger, get_player_manager
from core.game.player import Player
from events.buy_event import BuyEvent
from events.death_event import DeathEvent
from components.base.cost import Cost
from components.gameplay.squad import Squad
from core.ecs.iterator_system import IteratingProcessor


class EconomySystem(esper.Processor):
    def __init__(self, event_bus) -> None:
        super().__init__()
        self.event_bus = event_bus
        event_bus.subscribe(BuyEvent, self.buy)
        event_bus.subscribe(DeathEvent, self.reward_money)

        self.creation_time = pygame.time.get_ticks()
        self.generation_speed = 0.133  # Valeur de base pour 0-1 minute

    def buy(self, event):
        player: Player = event.player
        entity = event.entity
        money = player.money
        cost = esper.component_for_entity(entity, Cost)
        # money = esper.component_for_entity(player, Money)
        squad = esper.component_for_entity(player, Squad)

        if money >= cost.amount:
            money -= cost.amount
            squad.troops.append(entity)
            get_debugger().log(
                f"Vous avez acheté {entity} pour {cost.amount}. Il vous reste: {money} pépites d'or"
            )
        else:
            get_debugger().log(
                f"Il vous manqua {cost.amount - money} pour acheter {entity}"
            )

    def reward_money(self, event: DeathEvent):
        player_team: Team = event.player
        entity: int = event.entity
        if esper.has_component(entity, Cost):
            entity_cost = esper.component_for_entity(entity, Cost)
        else:
            entity_cost = Cost(0)
        player: Player = get_player_manager().players[player_team.team_id]

        reward = int(entity_cost.amount / 10)  # 10% du prix de l'entité

        if (
            player.money + reward >= 1500
        ):  # cap de thunes (à définir quelque part peut etre un fichier de constantes)
            player.money = 1500
        else:
            player.money += reward

        get_debugger().log(f"Vous avez tué {entity} et gagné {reward} pepites d'or")

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

        players: dict[int, Player] = get_player_manager().players
        # Ajout de la thune aux comptes des joueurs
        for team in players:
            if players[team].money + self.generation_speed >= 1500:  # Cap
                players[team].money = 1500
            else:
                players[team].money += self.generation_speed
