import esper
from components.base.team import Team
from core.ecs.component import Component


class Player(object):

    def __init__(
        self,
        team_number: int,
        bastion_id: int,
        start_money: int = 0,
        color: tuple[int] = (255, 255, 255),
        spawn_position: tuple[int, int] = (0, 0),
    ):
        self.team_number = team_number
        self.money: int = start_money
        self.bastion: int = bastion_id
        self.spawn_position: tuple[int, int] = spawn_position
        self.color: tuple[int] = color

    def get_bastion(self) -> tuple[Component]:
        """
        Get components of player bastion

        Returns:
            tuple[Component]: Components of player bastion
        """
        return esper.components_for_entity(self.bastion)
