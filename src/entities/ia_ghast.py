import random
from components.position import Position
from components.health import Health
from components.team import Team
from components.attack import Attack
from components.velocity import Velocity
from enums.entity_type import EntityType
from config.units import UNITS


class IAGhast:
    """
    IA avancée pour Ghast :
    - Se dirige vers la structure ennemie la plus proche.
    - Fuit si trop d'ennemis proches ou PV faibles.
    - Reste derrière ses alliés si possible.
    - S'arrête à portée d'attaque (range défini dans units.py).
    """

    ENEMY_RADIUS = 120
    ALLY_RADIUS = 80
    LOW_HEALTH = 40

    def __init__(self, ghast_entity, world):
        self.ghast = ghast_entity
        self.world = world
        self.target_building = None

        ghast_base = UNITS[EntityType.GHAST]
        print(ghast_base._components)
        self.stats = {}
        for comp in ghast_base._components:
            if isinstance(comp, Attack):
                self.stats["attack_range"] = comp.range
                print(comp.attack_speed, comp.range, comp.damage)

                self.stats["attack_speed"] = comp.attack_speed
                self.stats["damage"] = comp.damage
            elif isinstance(comp, Velocity):
                self.stats["speed"] = comp.speed
            elif isinstance(comp, Health):
                self.stats["max_health"] = comp.full

    def update(self):
        pos = self.world.component_for_entity(self.ghast, Position)
        health = self.world.component_for_entity(self.ghast, Health)
        team = self.world.component_for_entity(self.ghast, Team)

        if not (pos and health and team):
            return

        enemies = self._get_nearby_enemies(pos, team.team_id)
        if health.remaining < self.LOW_HEALTH or len(enemies) > 3:
            self._flee(pos, enemies)
            return

        allies = self._get_nearby_allies(pos, team.team_id)
        if allies:
            self._stay_behind_allies(pos, allies)
            return

        # Sélectionne le bâtiment ennemi le plus proche
        if not self.target_building or not self._entity_exists(self.target_building):
            self.target_building = self._find_enemy_building(team.team_id)

        if not self.target_building:
            return

        building_pos = self.world.component_for_entity(self.target_building, Position)
        if not building_pos:
            return

        # Vérifie la distance
        dist = ((building_pos.x - pos.x) ** 2 + (building_pos.y - pos.y) ** 2) ** 0.5

        if dist > self.stats["attack_range"]:
            self._move_towards(pos, building_pos)
        else:
            pass

    # ------------------------
    # Fonctions utilitaires
    # ------------------------

    def _entity_exists(self, entity_id):
        try:
            self.world.component_for_entity(entity_id, Position)
            return True
        except KeyError:
            return False

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
        target_ent = None
        ghast_pos = self.world.component_for_entity(self.ghast, Position)

        for ent, t in self.world.get_component(Team):
            if t.team_id != my_team_id:
                try:
                    entity_type = self.world.component_for_entity(ent, EntityType)
                except KeyError:
                    continue
                if entity_type == EntityType.BASTION:
                    ent_pos = self.world.component_for_entity(ent, Position)
                    dist = (
                        (ent_pos.x - ghast_pos.x) ** 2 + (ent_pos.y - ghast_pos.y) ** 2
                    ) ** 0.5
                    if dist < min_dist:
                        min_dist = dist
                        target_ent = ent

        return target_ent

    def _move_towards(self, pos, target_pos):
        speed = self.stats["speed"]
        dx = target_pos.x - pos.x
        dy = target_pos.y - pos.y
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            pos.x += speed * dx / dist
            pos.y += speed * dy / dist
