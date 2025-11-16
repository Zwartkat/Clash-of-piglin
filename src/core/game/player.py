import esper
from components.base.team import Team
from core.ecs.component import Component


class Player(object):

    def __init__(self, team_number: int, bastion_id: int, start_money: int = 100000):
        self.team_number = team_number
        self.money: int = start_money
        self.bastion: int = bastion_id

    def get_bastion(self) -> tuple[Component]:
        """
        Get components of player bastion

        Returns:
            tuple[Component]: Components of player bastion
        """
        return esper.components_for_entity(self.bastion)
