import esper
import pygame
from components.base.health import Health
from components.base.team import Team
from core import engine
from events.victory_event import VictoryEvent
from events.death_event import DeathEvent
from core.services import Services
from enums.entity.entity_type import EntityType


class VictorySystem(esper.Processor):

    def __init__(self):
        super().__init__()
        self.game_ended = False
        self.victory_message = ""

        Services.event_bus.subscribe(DeathEvent, self.on_entity_death)

    def on_entity_death(self, event: DeathEvent):
        """
        Check if entity who is die is an Bastion to trigger victory

        Args:
            event (DeathEvent): A death event
        """
        entity = event.entity

        if esper.has_component(entity, EntityType):
            entity_type: EntityType = esper.component_for_entity(entity, EntityType)
            if entity_type == EntityType.BASTION:

                if esper.has_component(entity, Team):
                    defeated_team_comp: Team = esper.component_for_entity(entity, Team)
                    defeated_team: int = defeated_team_comp.team_id

                    winning_team = 2 if defeated_team == 1 else 1

                    self.trigger_victory(winning_team, defeated_team)

    def handle_victory_input(self, event):
        """
        Manage game end

        Args:
            event (_type_): An input event

        Returns:
            bool: Game ended
        """
        if not self.game_ended:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                engine.game_state["running"] = False
                return True

    def trigger_victory(self, winning_team: int, losing_team: int):
        """
        Trigger a victory

        Args:
            winning_team (int): Id of winning team
            losing_team (int): Id of losing team
        """
        self.game_ended = True
        victory_event = VictoryEvent(winning_team, losing_team)
        Services.event_bus.emit(victory_event)
        Services.finish_time = pygame.time.get_ticks()

    def process(self, dt: float):
        if not self.game_ended:
            self.check_bastions_health()

    def check_bastions_health(self):
        """
        Check bastions health
        """
        if not Services.player_manager:
            return

        for team_id, player in Services.player_manager.players.items():
            try:
                if esper.has_component(player.bastion, Health):
                    health = esper.component_for_entity(player.bastion, Health)
                    if health.remaining <= 0:
                        winning_team = 2 if team_id == 1 else 1
                        self.trigger_victory(winning_team, team_id)
                        break
            except:
                winning_team = 2 if team_id == 1 else 1
                self.trigger_victory(winning_team, team_id)
                break
