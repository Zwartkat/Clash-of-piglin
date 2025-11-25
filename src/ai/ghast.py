import math
import esper
from components.base.position import Position
from components.base.team import Team
from components.base.velocity import Velocity
from components.gameplay.attack import Attack
from components.gameplay.structure import Structure
from enums.entity.entity_type import EntityType

from enum import Enum, auto


class JeromeGhastStates(Enum):
    OFFENSIVE = auto()
    SUPPORT = auto()


class JeromeGhast:
    def __init__(self, ent):
        self.state = JeromeGhastStates.OFFENSIVE
        self.ent = ent

    def decide(self):
        team = esper.component_for_entity(self.ent, Team).team_id
        team_adverse = 1 if team == 2 else 2
        pos = esper.component_for_entity(self.ent, Position)
        bastion_adverse = esper.get_component(Structure)[-team][0]
        bastion_adverse_pos = esper.component_for_entity(bastion_adverse, Position)
        velocity = esper.component_for_entity(self.ent, Velocity)
        portee = esper.component_for_entity(self.ent, Attack).range
        entities = esper.get_components(EntityType, Team, Position)
        crossbowmen = list(
            filter(
                lambda x: x[1][0] == EntityType.CROSSBOWMAN
                and x[1][1].team_id == team_adverse,
                entities,
            )
        )

        x, y = pos.getX(), pos.getY()

        if self.state == JeromeGhastStates.OFFENSIVE:
            dx_bastion, dy_bastion = (
                bastion_adverse_pos.getX() - x,
                bastion_adverse_pos.getY() - y,
            )

            dist_bastion = math.sqrt(dx_bastion**2 + dy_bastion**2)

            dir_x = dx_bastion / dist_bastion
            dir_y = dy_bastion / dist_bastion

            repulse_x, repulse_y = 0, 0

            for crossbowman in crossbowmen:
                pos_crossbow = crossbowman[1][2]
                range_crossbow = esper.component_for_entity(
                    crossbowman[0], Attack
                ).range
                cx, cy = pos_crossbow.getX(), pos_crossbow.getY()

                dx_crossbow, dy_crossbow = cx - x, cy - y

                dist_crossbow = math.sqrt(dx_crossbow**2 + dy_crossbow**2)

                if dist_crossbow < range_crossbow * 2:
                    force = (range_crossbow * 2 - dist_crossbow) / (range_crossbow * 2)
                    repulse_x += (x - cx) / dist_crossbow * force
                    repulse_y += (y - cy) / dist_crossbow * force

            if repulse_x == 0 and repulse_y == 0 and dist_bastion < portee:
                return

            # Pour fuir plus ou moins fort
            repulse_force = 3

            final_dx = dir_x + repulse_x * repulse_force
            final_dy = dir_y + repulse_y * repulse_force

            length = math.sqrt(final_dx**2 + final_dy**2)

            if length == 0:
                return

            final_dx /= length
            final_dy /= length

            old_x, old_y = x, y
            x += final_dx * velocity.speed
            y += final_dy * velocity.speed

            avance = (x - old_x) * dir_x + (y - old_y) * dir_y

            if avance <= 0:
                self.state = JeromeGhastStates.SUPPORT

            pos.setX(x)
            pos.setY(y)

        elif self.state == JeromeGhastStates.SUPPORT:
            # On garde que les crossbow car il ne peuvent pas tanker des brutes car elles n'attaquent pas les ghasts
            enemies = list(
                filter(
                    lambda x: x[1][1].team_id == team_adverse
                    and x[1][0] == EntityType.CROSSBOWMAN,
                    entities,
                )
            )
            allies = list(
                filter(lambda x: x[1][1].team_id == team and x[0] != self.ent, entities)
            )

            crossbow_in_bastion_range = False
            for enemy in enemies:
                enemy_pos = enemy[1][2]
                dx = enemy_pos.getX() - bastion_adverse_pos.getX()
                dy = enemy_pos.getY() - bastion_adverse_pos.getY()
                dist = math.sqrt(dx**2 + dy**2)
                range_enemy = esper.component_for_entity(enemy[0], Attack).range

                if dist <= range_enemy * 2:
                    crossbow_in_bastion_range = True
                    break

            if not crossbow_in_bastion_range:
                self.state = JeromeGhastStates.OFFENSIVE
                return

            dist_min = 999999

            for allie in allies:
                pos_allie = allie[1][2]
                ax, ay = pos_allie.getX(), pos_allie.getY()
                dist_allie = math.sqrt((ax - x) ** 2 + (ay - y) ** 2)

                if dist_allie < dist_min:
                    dist_min = dist_allie
                    pos_allie_proche = pos_allie

            dist_enemy_min = 999999

            for enemy in enemies:
                enemy_pos = enemy[1][2]
                ex, ey = enemy_pos.getX(), enemy_pos.getY()
                dist_enemy = math.sqrt(
                    (ex - pos_allie_proche.getX()) ** 2
                    + (ey - pos_allie_proche.getY()) ** 2
                )

                if dist_enemy < dist_enemy_min:
                    dist_enemy_min = dist_enemy
                    pos_enemy_proche = enemy_pos

            ax, ay = pos_allie_proche.getX(), pos_allie_proche.getY()
            ex, ey = pos_enemy_proche.getX(), pos_enemy_proche.getY()

            dx, dy = ex - ax, ey - ay
            dist = math.sqrt(dx**2 + dy**2)

            dir_x = dx / dist
            dir_y = dy / dist

            distance_defense = 20

            target_x = ax + dir_x * distance_defense
            target_y = ay + dir_y * distance_defense

            move_dx = target_x - x
            move_dy = target_y - y
            dist_move = math.sqrt(move_dx**2 + move_dy**2)

            if dist_move <= velocity.speed:
                return

            move_dx /= dist_move
            move_dy /= dist_move

            x += move_dx * velocity.speed
            y += move_dy * velocity.speed

            pos.setX(x)
            pos.setY(y)
