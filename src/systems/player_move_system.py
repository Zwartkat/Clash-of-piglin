import esper
from components.position import Position
from components.team import PLAYER_TEAM, Team
from components.velocity import Velocity
from events.event_move import EventMoveTo
from core.iterator_system import IteratingProcessor
from systems.troop_system import TROOP_CIRCLE, TROOP_GRID, FormationSystem


class PlayerMoveSystem(IteratingProcessor):
    def __init__(self, event_bus):
        super().__init__(Position, Velocity)
        self.event_bus = event_bus
        self.event_bus.subscribe(EventMoveTo, self.on_move)
        self.target = {}
        self.last_group_order = None

    def on_move(self, event):
        current_order = (event.target_x, event.target_y)

        if self.last_group_order == current_order:
            return

        self.last_group_order = current_order
        self.handle_group_order(event.target_x, event.target_y)

    def handle_group_order(self, target_x, target_y):
        player_entities = []
        for ent, (pos, vel, team) in esper.get_components(Position, Velocity, Team):
            if team.team_id == PLAYER_TEAM:
                player_entities.append(ent)

        positions = FormationSystem.calculate_formation_positions(
            player_entities, target_x, target_y, formation_type=TROOP_CIRCLE
        )

        for i, ent in enumerate(player_entities):
            if i < len(positions):
                target_x_formation, target_y_formation = positions[i]

                pos = esper.component_for_entity(ent, Position)
                vel = esper.component_for_entity(ent, Velocity)

                if pos and vel:
                    dx = target_x_formation - pos.x
                    dy = target_y_formation - pos.y
                    dist = (dx**2 + dy**2) ** 0.5
                    if dist > 0:
                        vel.x = (dx / dist) * 50
                        vel.y = (dy / dist) * 50
                        self.target[ent] = (target_x_formation, target_y_formation)

    def process_entity(self, ent, dt, pos, vel):
        if ent in self.target:
            tx, ty = self.target[ent]
            dx = tx - pos.x
            dy = ty - pos.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < 5:
                vel.x = 0
                vel.y = 0
                del self.target[ent]
