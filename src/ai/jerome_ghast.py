import math
import esper
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
from components.gameplay.attack import Attack
from components.gameplay.structure import Structure
from enums.entity.entity_type import EntityType

class JeromeGhast:
    def execute_action(self, ent):
        team = esper.component_for_entity(ent, Team).team_id
        pos = esper.component_for_entity(ent, Position)
        bastion_adverse = esper.get_component(Structure)[-team][0]
        bastion_adverse_pos = esper.component_for_entity(bastion_adverse, Position)
        velocity = esper.component_for_entity(ent, Velocity)
        portee = esper.component_for_entity(ent, Attack).range
        entities = esper.get_component(EntityType)
        crossbowmen = list(filter(lambda x: x[1] == EntityType.CROSSBOWMAN, entities))

        x, y = pos.getX(), pos.getY()

        dx_bastion, dy_bastion = bastion_adverse_pos.getX() - x, bastion_adverse_pos.getY() - y

        dist_bastion = math.sqrt(dx_bastion**2 + dy_bastion**2)

        if dist_bastion < portee:
            return

        dir_x = dx_bastion / dist_bastion
        dir_y = dy_bastion / dist_bastion

        repulse_x, repulse_y = 0, 0

        for crossbowman in crossbowmen:
            pos_crossbow = esper.component_for_entity(crossbowman[0], Position)
            range_crossbow = esper.component_for_entity(crossbowman[0], Attack).range
            cx, cy = pos_crossbow.getX(), pos_crossbow.getY()

            dx_crossbow, dy_crossbow = cx - x, cy - y

            dist_crossbow = math.sqrt(dx_crossbow**2 + dy_crossbow**2)

            if dist_crossbow < range_crossbow * 1.8:
                force = (range_crossbow * 1.8 - dist_crossbow) / (range_crossbow * 1.8)
                repulse_x += (x - cx) / dist_crossbow * force
                repulse_y += (y - cy) / dist_crossbow * force
        
        final_dx = dir_x + repulse_x
        final_dy = dir_y + repulse_y

        length = math.sqrt(final_dx**2 + final_dy**2)

        if length == 0:
            return
        
        final_dx /= length
        final_dy /= length

        x += final_dx * velocity.speed
        y += final_dy * velocity.speed

        pos.setX(x)
        pos.setY(y)