import random
from components.position import Position
from components.health import Health
from components.team import Team
from enums.entity_type import EntityType


class IAGhast:
    """
    IA avancée pour Ghast :
    - Se dirige vers la structure la plus proche.
    - Fuit si trop d'ennemis proches ou PV faibles.
    - Reste derrière ses alliés si possible.
    """

    ENEMY_RADIUS = 120  # Distance de détection des ennemis
    ALLY_RADIUS = 80  # Distance pour se protéger derrière alliés
    LOW_HEALTH = 40  # Seuil de PV faible

    def __init__(self, ghast_entity, world):
        self.ghast = ghast_entity
        self.world = world

    def update(self):
        pos = self.world.component_for_entity(self.ghast, Position)
        health = self.world.component_for_entity(self.ghast, Health)
        team = self.world.component_for_entity(self.ghast, Team)

        enemies = self._get_nearby_enemies(pos, team.team_id)
        if health.remaining < self.LOW_HEALTH or len(enemies) > 3:
            self._flee(pos, enemies)
            return

        allies = self._get_nearby_allies(pos, team.team_id)
        if allies:
            self._stay_behind_allies(pos, allies)
            return

        # Aller vers le bâtiment ennemi le plus proche
        enemy_building_pos = self._find_enemy_building(team.team_id)
        if enemy_building_pos:
            self._move_towards(pos, enemy_building_pos)

    def _get_nearby_enemies(self, pos, my_team):
        enemies = []
        for ent, t in self.world.get_component(Team):
            if t.team_id != my_team:
                ent_pos = self.world.component_for_entity(ent, Position)
                dist = ((ent_pos.x - pos.x) ** 2 + (ent_pos.y - pos.y) ** 2) ** 0.5
                if dist < self.ENEMY_RADIUS:
                    enemies.append(ent)
        return enemies

    def _get_nearby_allies(self, pos, my_team):
        allies = []
        for ent, t in self.world.get_component(Team):
            if t.team_id == my_team and ent != self.ghast:
                ent_pos = self.world.component_for_entity(ent, Position)
                dist = ((ent_pos.x - pos.x) ** 2 + (ent_pos.y - pos.y) ** 2) ** 0.5
                if dist < self.ALLY_RADIUS:
                    allies.append(ent)
        return allies

    def _flee(self, pos, enemies):
        # Fuit dans la direction opposée à la moyenne des ennemis
        if not enemies:
            return
        avg_x = sum(
            self.world.component_for_entity(e, Position).x for e in enemies
        ) / len(enemies)
        avg_y = sum(
            self.world.component_for_entity(e, Position).y for e in enemies
        ) / len(enemies)
        dx = pos.x - avg_x
        dy = pos.y - avg_y
        flee_x = pos.x + dx
        flee_y = pos.y + dy
        self._move_towards(pos, Position(flee_x, flee_y))

    def _stay_behind_allies(self, pos, allies):
        # Se place derrière le groupe d'alliés
        avg_x = sum(
            self.world.component_for_entity(a, Position).x for a in allies
        ) / len(allies)
        avg_y = sum(
            self.world.component_for_entity(a, Position).y for a in allies
        ) / len(allies)
        behind_x = avg_x - 20 + random.randint(-10, 10)
        behind_y = avg_y - 20 + random.randint(-10, 10)
        self._move_towards(pos, Position(behind_x, behind_y))

    def _find_enemy_building(self, my_team_id):
        min_dist = float("inf")
        target_pos = None
        ghast_pos = self.world.component_for_entity(self.ghast, Position)
        for ent, t in self.world.get_component(Team):
            if t.team_id != my_team_id:
                # Vérifie que l'entité est un bastion ennemi
                if self.world.has_component(ent, EntityType):
                    entity_type = self.world.component_for_entity(ent, EntityType)
                    if entity_type == EntityType.BASTION:
                        ent_pos = self.world.component_for_entity(ent, Position)
                        dist = (
                            (ent_pos.x - ghast_pos.x) ** 2
                            + (ent_pos.y - ghast_pos.y) ** 2
                        ) ** 0.5
                        if dist < min_dist:
                            min_dist = dist
                            target_pos = ent_pos
        return target_pos

    def _move_towards(self, pos, target_pos):
        """
        Déplace le Ghast vers la position cible.
        """
        speed = 2  # Vitesse de déplacement
        dx = target_pos.x - pos.x
        dy = target_pos.y - pos.y
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            pos.x += speed * dx / dist
            pos.y += speed * dy / dist
