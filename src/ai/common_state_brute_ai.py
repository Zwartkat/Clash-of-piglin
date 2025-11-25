import esper
from core.entity import Entity
from core.event_bus import EventBus
from components.team import Team
from components.position import Position
from events.spawn_unit_event import SpawnUnitEvent
from events.death_event import DeathEvent
from events.attack_event import AttackEvent
from events.event_move import EventMoveTo


class CommonState:

    def __init__(self):
        self.units: dict[Team, Entity] = {}
        self.groups: list[list[Entity]] = []

        # EventBus.get_event_bus().subscribe(SpawnUnitEvent, self.)
