from components.team import Team


class VictoryEvent:
    def __init__(self, winning_team: Team, losing_team: Team):
        self.winning_team: Team = winning_team
        self.losing_team: Team = losing_team
