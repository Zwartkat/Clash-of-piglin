import esper
from components.position import Position
from components.velocity import Velocity
from events.event_move import EventMoveTo

class PlayerMoveSystem(esper.Processor):
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.event_bus.subscribe(EventMoveTo, self.on_move)
        self.target = None  # (entity, x, y)

    def on_move(self, event):
        pos = esper.component_for_entity(event.entity, Position)
        vel = esper.component_for_entity(event.entity, Velocity)
        dx = event.target_x - pos.x
        dy = event.target_y - pos.y
        dist = (dx**2 + dy**2)**0.5
        if dist > 0:
            vel.x = (dx / dist) * 50
            vel.y = (dy / dist) * 50
            self.target = (event.entity, event.target_x, event.target_y)

    def process(self, dt):
        if self.target:
            entity, tx, ty = self.target
            pos = esper.component_for_entity(entity, Position)
            vel = esper.component_for_entity(entity, Velocity)
            dx = tx - pos.x
            dy = ty - pos.y
            dist = (dx**2 + dy**2)**0.5
            if dist < 2:  # seuil d'arrêt
                vel.x = 0
                vel.y = 0
                self.target = None