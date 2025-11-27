import esper
from core.entity import Entity
from core.event_bus import EventBus
from components.team import Team
from components.position import Position
from components.health import Health
from components.attack import Attack
from enums.entity_type import EntityType
from events.spawned_unit_event import SpawnedUnitEvent
from events.death_event import DeathEvent


class CommonState:

    def __init__(self):
        self.event_bus = EventBus.get_event_bus()
        self.units: dict[Team, list[int]] = {}
        self.groups: dict[int, list[int]] = {}
        self.default_group: list[Entity] = []
        self.group_index = 0

        for entity, (entity_type, team) in esper.get_components(EntityType, Team):
            self.add_unit(entity_type, team, entity)

        self.event_bus.subscribe(SpawnedUnitEvent, self.add_unit_on_spawn)
        self.event_bus.subscribe(DeathEvent, self.remove_unit)

    def add_unit(self, entity_type: EntityType, team: Team, entity: int):
        if entity_type != EntityType.BASTION:
            self.units.setdefault(team.team_id, []).append(entity)
            if entity_type == EntityType.CROSSBOWMAN:
                self.add_to_group_on_spawn(entity)
            else:
                self.default_group.append(entity)
            # print(self.units)

    def add_unit_on_spawn(self, spawn_event: SpawnedUnitEvent):
        self.add_unit(
            esper.component_for_entity(spawn_event.entity_id, EntityType),
            esper.component_for_entity(spawn_event.entity_id, Team),
            spawn_event.entity_id,
        )

    def remove_unit(self, death_event: DeathEvent):
        entity_team = esper.component_for_entity(death_event.entity, Team)
        self.units[entity_team.team_id].remove(death_event.entity)
        # print(self.units)

    def add_to_new_group(self, entity: int):
        self.groups.setdefault(self.group_index, []).append(entity)
        self.group_index += 1
        print(self.groups)
        print(self.default_group)

    def add_to_group_on_spawn(self, entity_to_add: int):
        range = esper.component_for_entity(entity_to_add, Attack).range
        position = esper.component_for_entity(entity_to_add, Position)
        team = esper.component_for_entity(entity_to_add, Team).team_id

        for group in self.groups:
            # print(group, entity_to_add)
            for entity in self.groups[group]:
                troup_x = esper.component_for_entity(entity, Position).getX()
                troup_y = esper.component_for_entity(entity, Position).getY()
                troup_team = esper.component_for_entity(entity, Team).team_id
                if (
                    (
                        troup_x <= position.getX() + range
                        and troup_x >= position.getX() - range
                    )
                    and (
                        troup_y <= position.getY() + range
                        and troup_y >= position.getY() - range
                    )
                    and troup_team == team
                ):
                    self.groups[group].append(entity_to_add)
                    # print(self.groups)
                    # print(self.default_group)
                    return

        self.add_to_new_group(entity_to_add)
        # print(self.groups)
        # print(self.default_group)
