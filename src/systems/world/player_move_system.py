import esper
from components.base.position import Position
from components.base.velocity import Velocity
from core.accessors import get_event_bus
from events.event_move import EventMoveTo
from core.ecs.iterator_system import IteratingProcessor
from systems.combat.troop_system import TROOP_CIRCLE, TROOP_GRID, FormationSystem
from components.gameplay.selection import Selection

from core.ecs.event_bus import EventBus
from events.stop_event import StopEvent


class PlayerMoveSystem(IteratingProcessor):
    """Handles unit movement when player gives move orders."""

    def __init__(self):
        super().__init__(Position, Velocity)
        get_event_bus().subscribe(EventMoveTo, self.on_move)
        self.target = {}
        self.last_group_order = None

    def on_move(self, event):
        """
        Start moving entity to target position when move order is given.

        Args:
            event: EventMoveTo with entity ID and target position
        """
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
        """
        Update entity movement towards target and stop when close enough.

        Args:
            ent: Moving entity ID
            dt: Time passed since last frame
            pos: Entity current position
            vel: Entity velocity to update
        """
        if ent in self.target:
            tx, ty = self.target[ent]
            dx = tx - pos.x
            dy = ty - pos.y
            dist = (dx**2 + dy**2) ** 0.5

            # Stop when close to target
            if dist < 5:
                vel.x = 0
                vel.y = 0
                del self.target[ent]
                get_event_bus().emit(StopEvent(ent))

                # Deselect unit when it reaches destination
                selection = esper.component_for_entity(ent, Selection)
                if selection:
                    selection.is_selected = False
            else:
                # Keep moving towards target
                speed = 100
                vel.x = (dx / dist) * speed
                vel.y = (dy / dist) * speed
