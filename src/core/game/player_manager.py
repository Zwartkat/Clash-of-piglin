import esper
from ai.ai_bastion import AiBastion
from components.ai_controller import AIController
from core.accessors import get_config, get_debugger, get_map
from core.game.map import Map
from core.game.player import Player
from components.base.position import Position
from components.base.team import PLAYER_1_TEAM, PLAYER_2_TEAM, Team
from core.config import Config
from enums.entity.entity_type import EntityType
from factories.entity_factory import EntityFactory
from factories.unit_factory import UnitFactory


class PlayerManager:
    def __init__(self, ai_player_1: bool = False, ai_player_2: bool = True):

        self.players: dict[int, Player] = {}

        map: Map = get_map()
        tile_size: int = get_config().get("tile_size", 32)
        map_size: int = len(map.tab) * tile_size

        self._create_player(
            1,
            Position(tile_size * 2, tile_size * 2),
            Position(tile_size * 2, tile_size * 2),
            (255, 85, 85),
            300,
            ai_player_1,
        )
        self._create_player(
            2,
            Position(map_size - tile_size * 2, map_size - tile_size * 2),
            Position(map_size - tile_size * 3, map_size - tile_size * 3),
            (20, 180, 133),
            300,
            ai_player_2,
        )

        self.current_player = 1

    def _create_player(
        self,
        team_number: int,
        bastion_pos: Position,
        spawn_position: Position,
        color: tuple[int],
        start_money: int = 0,
        ai_active: bool = False,
    ) -> Player:
        bastion = UnitFactory.create_unit(
            EntityType.BASTION,
            Team(team_number),
            bastion_pos,
        )
        player = Player(
            team_number,
            bastion,
            start_money=start_money,
            color=color,
            spawn_position=spawn_position,
        )
        self.players[team_number] = player

        if ai_active:
            esper.add_component(
                bastion, AIController(bastion, AiBastion(team_number), None)
            )
        return player

    def switch_player(self):

        self.current_player = (self.current_player % len(self.players)) + 1

    def get_current_player(self) -> Player | None:
        if self.players[self.current_player]:
            return self.players[self.current_player]
        else:
            return None

    def get_enemy_player(self, team: int) -> Player | None:

        if team == 1:
            return self.players[2]
        elif team == 2:
            return self.players[1]
        else:
            get_debugger().error(
                f"Player manager : Unknown team id for 'get_enemy_player()'"
            )

    def get_current_player_number(self) -> int:
        return self.current_player

    def is_current_player(self, team_id: int) -> bool:
        return team_id == self.get_current_player()
