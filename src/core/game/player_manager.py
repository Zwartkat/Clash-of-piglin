from core.game.player import Player
from components.base.position import Position
from components.base.team import PLAYER_1_TEAM, PLAYER_2_TEAM, Team
from core.config import Config
from enums.entity.entity_type import EntityType
from factories.entity_factory import EntityFactory
from factories.unit_factory import UnitFactory


class PlayerManager:
    def __init__(self, bastions: list[Position]):

        if len(bastions) <= 1:
            raise Exception("You must have at least 2 players.")

        self.players: dict[int,] = {}
        team: int = 1

        for bastion_pos in bastions:
            bastion = UnitFactory.create_unit(
                EntityType.BASTION,
                Team(team),
                bastion_pos,
            )
            self.players[team] = Player(team, bastion, start_money=1000)
            team += 1

        self.current_player = 1

    def switch_player(self):

        self.current_player = (self.current_player % len(self.players)) + 1

    # def get_current_player(self) -> Player | None:
    #    if self.players[self.current_player]:
    #        return self.players[self.current_player]
    #    else :
    #        return None

    def get_enemy_player(self, team: int) -> Player:
        return self.players[team + 1 % self.players.__len__()]

    def get_current_player(self) -> int:
        return self.current_player

    def is_current_player(self, team_id: int) -> bool:
        return team_id == self.get_current_player()
