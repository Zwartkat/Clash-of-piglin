import math
import esper
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
from components.gameplay.attack import Attack
from components.gameplay.structure import Structure

class JeromeGhast:
    def execute_action(self, ent):
        team = esper.component_for_entity(ent, Team).team_id
        pos = esper.component_for_entity(ent, Position)
        bastion_adverse = esper.get_component(Structure)[-team][0]
        bastion_adverse_pos = esper.component_for_entity(bastion_adverse, Position)
        velocity = esper.component_for_entity(ent, Velocity)
        range = esper.component_for_entity(ent, Attack).range

        x, y = pos.getX(), pos.getY()

        dx, dy = bastion_adverse_pos.getX() - x, bastion_adverse_pos.getY() - y

        distance = math.sqrt(dx**2 + dy**2)

        if distance < range:
            return

        dx /= distance
        dy /= distance

        x += dx * velocity.speed
        y += dy * velocity.speed

        pos.setX(x)
        pos.setY(y)