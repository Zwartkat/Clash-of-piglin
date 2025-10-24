import random
from components.position import Position
from components.health import Health
from components.team import Team
from components.attack import Attack
from components.velocity import Velocity
from enums.entity_type import EntityType
from config.units import UNITS

##TODO : Esquiver la range des enemis
#
# Si base alliés a peu de PV, attaquer a tout prix
# Si base ennemie a peu de PV, attaquer a tout prix
# Mettre un système de notation pour chaque action possible et choisir la meilleure ?


class IAGhast:
    """
    IA avancée pour Ghast :
    - Se dirige vers la structure ennemie la plus proche.
    - Fuit si trop d'ennemis proches ou PV faibles.
    - Reste derrière ses alliés si possible.
    - S'arrête à portée d'attaque (range défini dans units.py).
    """

    LOW_HEALTH = 30

    def __init__(self, ghast_entity, world):
        self.ghast = ghast_entity
        self.world = world
        self.target_building = None

        ghast_base = UNITS[EntityType.GHAST]
        self.stats = {}
        for comp in ghast_base._components:
            if isinstance(comp, Attack):
                self.stats["attack_range"] = comp.range
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

        ally_base, enemy_base = self._get_bases(team.team_id)

        if not self.target_building or not self._entity_exists(self.target_building):
            print("- Finding new target building")
            self.target_building = self._find_enemy_building(team.team_id)

        if not self.target_building:
            print("- No target building found")
            return

        building_pos = self.world.component_for_entity(self.target_building, Position)

        enemies = []
        for ent, t in self.world.get_component(Team):
            if t.team_id != team.team_id:
                enemies.append(ent)

        ## Si ally à une distance > 80 ally = None
        ally = self._get_closest_ally(pos, team.team_id)
        if ally and ally[1] > 80:
            ally = None

        ##décision en cours
        print("IA Ghast update called")
        print("Position:", pos)
        print("Health:", health.remaining)
        print("Enemies nearby:", self._get_number_enemies_near(pos, team.team_id))
        print("Position ally nearby:", self._get_closest_ally(pos, team.team_id))
        print("Decisions en cours:")

        if ally_base and ally_base[1].remaining < 100:
            print(" Near deffeat, attack at all cost")
            self._move_towards(pos, building_pos)
        elif enemy_base and enemy_base[1].remaining < 100:
            print(" Near victory, attack at all cost")
            self._move_towards(pos, building_pos)

        # Fuir si PV bas
        if health.remaining < self.LOW_HEALTH:
            print("- Fleeing due to low health")
            self._flee(pos, enemies)
            return

        # Fuir si trop d'ennemis proches
        if self._get_number_enemies_near(pos, team.team_id)[0] > 2:
            print("- Fleeing due to too many nearby enemies")
            self._flee(pos, enemies)
            return

        # Voir si c'est bénéfique de rester derrière un allié en fonction de la distance ennemie
        if ally and self._get_number_enemies_near(pos, team.team_id)[1] < 90:
            print("- Staying behind ally")
            self._stay_behind_ally(pos, ally)
            return

        # Voir si c'est bénéfique d'attaquer en fonction du nombre d'alliés et d'ennemis totaux
        # (si moins d'ennemis que d'alliés, attaquer, sinon rester proche de la base)

        dist = ((building_pos.x - pos.x) ** 2 + (building_pos.y - pos.y) ** 2) ** 0.5
        total_enemies = len(self._get_all_enemies(pos, team.team_id))
        print("Total enemies:", total_enemies)
        total_allies = len(self._get_all_allies(pos, team.team_id))
        print("Total allies:", total_allies)
        if total_enemies <= total_allies:
            # Attaquer si à portée
            if dist > self.stats["attack_range"]:
                print("- Moving towards target building")
                self._move_towards(pos, building_pos)
        else:
            print("- Staying near base")
            self._stay_near_base(pos)

    # ------------------------
    # Fonctions utilitaires
    # ------------------------

    def _entity_exists(self, entity_id):
        try:
            self.world.component_for_entity(entity_id, Position)
            return True
        except KeyError:
            return False

    def _get_all_enemies(self, pos, my_team) -> list:
        enemies = []
        for ent, t in self.world.get_component(Team):
            if t.team_id != my_team:
                enemies.append(ent)
        return enemies

    def _get_all_allies(self, pos, my_team) -> list:
        allies = []
        for ent, t in self.world.get_component(Team):
            if t.team_id == my_team and ent != self.ghast:
                allies.append(ent)
        return allies

    def _get_number_enemies_near(self, pos, my_team) -> list:
        """
        Retourne le nombre d'ennemis à proximité.
        """
        nb_enemies = 0
        dist = float("inf")
        for ent, t in self.world.get_component(Team):
            if t.team_id != my_team:
                ent_pos = self.world.component_for_entity(ent, Position)
                dist = ((ent_pos.x - pos.x) ** 2 + (ent_pos.y - pos.y) ** 2) ** 0.5
                if dist < 150:
                    nb_enemies += 1
        return [nb_enemies, dist]

    def _get_closest_ally(self, pos, my_team):
        """
        Retourne l'allié le plus proche, et sa distance.
        """
        ally = None
        min_dist = float("inf")
        for ent, t in self.world.get_component(Team):
            if t.team_id == my_team and ent != self.ghast:
                ent_pos = self.world.component_for_entity(ent, Position)
                dist = ((ent_pos.x - pos.x) ** 2 + (ent_pos.y - pos.y) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    ally = [ent, dist, ent_pos]
        return ally

    def _flee_range_enemy(self, pos, my_team):
        enemy = []
        for ent, t in self.world.get_component(Team):
            if t.team_id != my_team:
                if ent == UNITS[EntityType.CROSSBOWMAN]:
                    ent_pos = self.world.component_for_entity(ent, Position)
                    dist = ((ent_pos.x - pos.x) ** 2 + (ent_pos.y - pos.y) ** 2) ** 0.5
                    if dist < +30:
                        enemy.append((ent_pos, dist))
        if not enemy:
            return

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

    def _stay_behind_ally(self, pos, ally):
        """
        Reste derrière l'allié donné à une distance de 40 pixels.
        """
        if not ally:
            return
        ally_pos = ally[2]
        dx = pos.x - ally_pos.x
        dy = pos.y - ally_pos.y
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 40:
            target_x = ally_pos.x + (dx / dist) * 40
            target_y = ally_pos.y + (dy / dist) * 40
            self._move_towards(pos, Position(target_x, target_y))

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

    def _stay_near_base(self, pos):
        """
        Reste proche de la base alliée (position (50, 50) pour l'équipe 1, (730, 730) pour l'équipe 2).
        """
        base_pos = (
            Position(50, 50)
            if self.world.component_for_entity(self.ghast, Team).team_id == 1
            else Position(730, 730)
        )
        dist = ((base_pos.x - pos.x) ** 2 + (base_pos.y - pos.y) ** 2) ** 0.5
        if dist > 100:
            self._move_towards(pos, base_pos)

    def _get_bases(self, my_team_id):
        ally_base = None
        enemy_base = None
        for ent, t in self.world.get_component(Team):
            try:
                etype = self.world.component_for_entity(ent, EntityType)
            except KeyError:
                continue
            if etype == EntityType.BASTION:
                h = self.world.component_for_entity(ent, Health)
                if t.team_id == my_team_id:
                    ally_base = (ent, h)
                else:
                    enemy_base = (ent, h)
        return ally_base, enemy_base
