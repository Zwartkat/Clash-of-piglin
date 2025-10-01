import esper
from components.position import Position
from components.velocity import Velocity
from events.event_move import EventMoveTo
from core.iterator_system import IteratingProcessor
from systems.troop_system import TROOP_CIRCLE, TROOP_GRID, FormationSystem
from components.selection import Selection

from core.event_bus import EventBus
from events.stop_event import StopEvent


class PlayerMoveSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Position, Velocity)
        EventBus.get_event_bus().subscribe(EventMoveTo, self.on_move)
        self.target = {}
        self.last_group_order = None

    def on_move(self, event):
        pos = esper.component_for_entity(event.entity, Position)
        vel = esper.component_for_entity(event.entity, Velocity)

        if pos and vel:
            dx = event.target_x - pos.x
            dy = event.target_y - pos.y
            dist = (dx**2 + dy**2) ** 0.5

            if dist > 0:
                speed = 100
                vel.x = (dx / dist) * speed
                vel.y = (dy / dist) * speed
                self.target[event.entity] = (event.target_x, event.target_y)

    def process_entity(self, ent: int, dt: float, pos: Position, vel: Velocity):
        if ent in self.target:
            tx, ty = self.target[ent]
            dx = tx - pos.x
            dy = ty - pos.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < 5:
                vel.x = 0
                vel.y = 0
                del self.target[ent]
                EventBus.get_event_bus().emit(StopEvent(ent))

                selection = esper.component_for_entity(ent, Selection)
                if selection:
                    selection.is_selected = False
            else:
                speed = 100
                vel.x = (dx / dist) * speed
                vel.y = (dy / dist) * speed
