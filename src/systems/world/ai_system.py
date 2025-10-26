import esper
from enums.entity.entity_type import *
from components.base.position import Position
from components.base.velocity import Velocity
from components.base.description import Description
from components.gameplay.attack import Attack
from components.gameplay.structure import Structure
from components.base.team import *
from core.game.map import Map
from components.base.ai_flag import Ai_flag
from core.ecs.iterator_system import IteratingProcessor

class AISystem(IteratingProcessor):

    def __init__(self):
        super().__init__(Position, Velocity)
        self.map = None
        self.map_size = 0

#-----------------------------------------------------------
#                   Fonctions utiles
#-----------------------------------------------------------

    def get_map_data(self):
        """Récupère les données de la map depuis le monde ECS"""
        if not self.map:
            maps = list(esper.get_component(Map))
            if maps:
                self.map = maps[0][1]  # Prendre le premier composant Map trouvé
                self.map_size = len(self.map.tab)

    def is_position_accessible(self, x, y):
        """Vérifie si une position est accessible (pas de LAVA et dans les limites)"""
        if x < 0 or y < 0 or x >= self.map_size or y >= self.map_size:
            return False

        case_type = self.map.tab[x][y].getType()
        return case_type not in Map.restricted_cases

    def find_path_around_obstacles(self, start_pos, target_pos, attack_range):
        """
        Trouve un chemin pour contourner les obstacles vers la cible
        en utilisant un algorithme de recherche en largeur (BFS)
        """
        self.get_map_data()
        if not self.map:
            return target_pos  # Retourne la cible directe si pas de map

        # Si la position de départ n'est pas accessible, trouver la position accessible la plus proche
        if not self.is_position_accessible(int(start_pos.x), int(start_pos.y)):
            accessible_pos = self.find_nearest_accessible_position(start_pos)
            if accessible_pos:
                return accessible_pos
            else:
                return start_pos  # Reste sur place si aucun chemin trouvé

        # Vérifier si on peut atteindre la cible directement
        if self.is_direct_path_clear(start_pos, target_pos):
            return self.get_in_range(start_pos, target_pos, attack_range)

        # Sinon, chercher un chemin avec BFS
        path = self.bfs_pathfinding(start_pos, target_pos)
        if path and len(path) > 1:
            # Retourne la prochaine position sur le chemin
            return path[1]
        else:
            # Si aucun chemin trouvé, essayer de se rapprocher autant que possible
            return self.get_closest_accessible_position(start_pos, target_pos)

    def is_direct_path_clear(self, start_pos, target_pos):
        """Vérifie si le chemin direct entre start_pos et target_pos est dégagé"""
        # Algorithme de ligne de vue (Bresenham)
        x0, y0 = int(start_pos.x), int(start_pos.y)
        x1, y1 = int(target_pos.x), int(target_pos.y)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            if not self.is_position_accessible(x, y):
                return False
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx

        return True

    def bfs_pathfinding(self, start_pos, target_pos, max_depth=50):
        """
        Algorithme BFS pour trouver un chemin évitant les obstacles
        """
        start = (int(start_pos.x), int(start_pos.y))
        target = (int(target_pos.x), int(target_pos.y))

        if start == target:
            return [start_pos]

        queue = [start]
        visited = {start: None}
        depth = 0

        while queue and depth < max_depth:
            current = queue.pop(0)
            depth += 1

            if current == target:
                # Reconstruire le chemin
                path = []
                while current != start:
                    path.append(Position(current[0], current[1]))
                    current = visited[current]
                path.reverse()
                return path

            # Explorer les voisins
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor = (current[0] + dx*50, current[1] + dy*50)

                if (neighbor not in visited and self.is_position_accessible(neighbor[0], neighbor[1])):
                    visited[neighbor] = current
                    queue.append(neighbor)

        return None  # Aucun chemin trouvé

    def find_nearest_accessible_position(self, position):
        """Trouve la position accessible la plus proche"""
        x, y = int(position.x), int(position.y)

        # Chercher en spirale autour de la position
        for radius in range(1, min(10, self.map_size)):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Seulement le périmètre
                        new_x, new_y = x + dx, y + dy
                        if self.is_position_accessible(new_x, new_y):
                            return Position(new_x, new_y)
        return None

    def get_closest_accessible_position(self, start_pos, target_pos):
        """
        Trouve la position accessible la plus proche de la cible
        en partant de la position de départ
        """
        target_x, target_y = int(target_pos.x), int(target_pos.y)
        start_x, start_y = int(start_pos.x), int(start_pos.y)

        best_pos = start_pos
        min_distance = float('inf')

        # Chercher dans un rayon autour de la cible
        for radius in range(1, min(15, self.map_size)):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) <= radius and abs(dy) <= radius:
                        test_x, test_y = target_x + dx, target_y + dy
                        if (self.is_position_accessible(test_x, test_y) and
                            self.is_direct_path_clear(start_pos, Position(test_x, test_y))):

                            distance = ((test_x - target_x)**2 + (test_y - target_y)**2) ** 0.5
                            if distance < min_distance:
                                min_distance = distance
                                best_pos = Position(test_x, test_y)

        return best_pos

    def move_towards(self, pos, target_pos, speed):
        dx = target_pos.x - pos.x
        dy = target_pos.y - pos.y
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            pos.x += speed * dx / dist
            pos.y += speed * dy / dist

    def get_in_range(self, current_pos, target_pos, attack_range):
        """
        Calcule la position où s'arrêter pour être à portée d'attaque sans être en corps à corps
        """
        dx = target_pos.x - current_pos.x
        dy = target_pos.y - current_pos.y
        dist = (dx**2 + dy**2) ** 0.5

        # Si déjà à bonne distance, ne pas bouger
        if dist <= attack_range:
            return current_pos

        # Calculer la position à la distance d'attaque
        if dist > 0:
            # Réduire la distance de la portée d'attaque
            move_dist = dist - attack_range
            ratio = move_dist / dist

            new_x = current_pos.x + dx * ratio
            new_y = current_pos.y + dy * ratio

            return Position(new_x, new_y)

        return current_pos

    def is_unit_threatened(self, unit_ent):
        """
        Vérifie si une unité est trop proche d'un ennemi (moins de 65% de sa portée d'attaque)
        Retourne True si l'unité est en danger, False sinon
        """
        # Récupérer les composants de l'unité
        unit_pos = esper.component_for_entity(unit_ent, Position)
        unit_team = esper.component_for_entity(unit_ent, Team)
        unit_attack = esper.component_for_entity(unit_ent, Attack)

        # Calculer la distance de danger (65% de la portée d'attaque)
        danger_distance = unit_attack.range * 0.65

        # Parcourir toutes les entités pour trouver les ennemis
        for ent, (pos, team) in esper.get_components(Position, Team):
            # Ignorer l'unité elle-même et les alliés
            if ent == unit_ent or team.team_id == unit_team.team_id:
                continue

            # Calculer la distance avec l'ennemi
            dx = pos.x - unit_pos.x
            dy = pos.y - unit_pos.y
            distance = (dx**2 + dy**2) ** 0.5

            # Si un ennemi est trop proche, l'unité est en danger
            if distance <= danger_distance:
                return True

        return False

    def get_ennemy_bastion(self, self_team):

        return esper.get_component(Structure)[-self_team][0]

    def get_units(self, searched_unit:EntityType=EntityType.BRUTE):
        unit_sorted = [[],[]]
        unit_list = esper.get_component(EntityType)
        unit_list = list(filter(lambda x: x[1] == searched_unit, unit_list))
        for ent in unit_list:
            team = esper.component_for_entity(ent[0], Team)
            pos = esper.component_for_entity(ent[0], Position)
            if team.team_id == PLAYER_1_TEAM:
                unit_sorted[0].append((ent[0], pos, team))
            elif team.team_id == PLAYER_2_TEAM:
                unit_sorted[1].append((ent[0], pos, team))
        return unit_sorted

    def find_nearest_ally_ghast(self, self_ent, self_team, max_distance=350):
        """
        Trouve le Ghast allié le plus proche
        """
        nearest_ghast = None
        min_distance = float('inf')

        # Parcourir toutes les entités pour trouver les Ghast alliés
        for ent, (entity_type, team, pos) in esper.get_components(EntityType, Team, Position):
            if (ent != self_ent and
                team.team_id == self_team and
                entity_type == EntityType.GHAST):

                # Calculer la distance avec le Ghast
                self_pos = esper.component_for_entity(self_ent, Position)
                dx = pos.x - self_pos.x
                dy = pos.y - self_pos.y
                distance = (dx**2 + dy**2) ** 0.5

                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    nearest_ghast = (ent, pos)

        return nearest_ghast

    def find_nearest_enemy_crossbow(self, self_ent, self_team, max_distance=450):
        """
        Trouve l'archer ennemi (Crossbow) le plus proche
        """
        nearest_crossbow = None
        min_distance = float('inf')

        # Parcourir toutes les entités pour trouver les Crossbow ennemis
        for ent, (entity_type, team, pos) in esper.get_components(EntityType, Team, Position):
            if (ent != self_ent and
                team.team_id != self_team and
                entity_type == EntityType.CROSSBOWMAN):

                # Calculer la distance avec l'archer ennemi
                self_pos = esper.component_for_entity(self_ent, Position)
                dx = pos.x - self_pos.x
                dy = pos.y - self_pos.y
                distance = (dx**2 + dy**2) ** 0.5

                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    nearest_crossbow = (ent, pos)

        return nearest_crossbow

    def get_attack_range(self, ent):
        """Récupère la portée d'attaque d'une entité"""
        if esper.has_component(ent, Attack):
            return esper.component_for_entity(ent, Attack).range
        return 0

#-----------------------------------------------------------
#                Comportements principaux
#-----------------------------------------------------------

    def coward_behavior(self, self_ent, self_team, self_pos, self_vel):
        """Recule hors de portée de l'adversaire"""
        self_attack = esper.component_for_entity(self_ent, Attack)
        self_range = self_attack.range
        self_speed = esper.component_for_entity(self_ent, Velocity).speed

        # Trouver l'ennemi le plus proche
        closest_enemy = None
        min_distance = float('inf')

        for ent, (pos, team) in esper.get_components(Position, Team):
            if team.team_id != self_team and ent != self_ent:
                dx = pos.x - self_pos.x
                dy = pos.y - self_pos.y
                distance = (dx**2 + dy**2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    closest_enemy = pos

        # Si un ennemi est trouvé, s'en éloigner en évitant les obstacles
        if closest_enemy:
            # Calculer la direction opposée
            dx = self_pos.x - closest_enemy.x
            dy = self_pos.y - closest_enemy.y
            dist = (dx**2 + dy**2) ** 0.5

            if dist > 0:
                # Calculer la position de fuite
                flee_distance = self_range * 1.5  # Fuir à 150% de la portée
                flee_x = self_pos.x + (dx / dist) * flee_distance
                flee_y = self_pos.y + (dy / dist) * flee_distance
                flee_pos = Position(flee_x, flee_y)

                # Trouver un chemin safe pour fuir
                safe_flee_pos = self.find_path_around_obstacles(self_pos, flee_pos, 0)
                self.move_towards(self_pos, safe_flee_pos, self_speed)

    def attack_behavior(self, self_ent, self_team, self_pos, self_vel): #foncer sur le bastion
        ennemy_bastion = self.get_ennemy_bastion(self_team)
        ennemy_bastion_pos = esper.component_for_entity(ennemy_bastion, Position)

        self_attack = esper.component_for_entity(self_ent, Attack)
        self_range = self_attack.range
        self_speed = esper.component_for_entity(self_ent, Velocity)
        self_speed = self_speed.speed

        safe_target = self.find_path_around_obstacles(self_pos, ennemy_bastion_pos, self_range)

        # Se déplacer vers la position safe
        stop_position = self.get_in_range(self_pos, safe_target, self_range)
        self.move_towards(self_pos, stop_position, self_speed)


    def support_behavior(self, self_ent, self_team, self_pos, self_vel):
        """
        Comportement de support : rester près d'un Ghast allié et prioriser les Crossbow ennemis
        """
        self_attack = esper.component_for_entity(self_ent, Attack)
        self_range = self_attack.range
        self_speed = esper.component_for_entity(self_ent, Velocity).speed

        # 1. Chercher un Ghast allié à proximité
        nearest_ghast = self.find_nearest_ally_ghast(self_ent, self_team)

        # 2. Chercher un Crossbow ennemi à portée
        nearest_crossbow = self.find_nearest_enemy_crossbow(self_ent, self_team, self_range * 1.5)

        print(nearest_ghast)
        # 3. Si un Crossbow ennemi est à portée, le prioriser
        if nearest_crossbow:
            crossbow_ent, crossbow_pos = nearest_crossbow

            # Se positionner à portée d'attaque du Crossbow
            safe_target = self.find_path_around_obstacles(self_pos, crossbow_pos, self_range)
            stop_position = self.get_in_range(self_pos, safe_target, self_range)
            self.move_towards(self_pos, stop_position, self_speed)

        # 4. Sinon, si un Ghast allié est trouvé, rester à proximité

        elif nearest_ghast:
            ghast_ent, ghast_pos = nearest_ghast

            # Calculer la position idéale : à mi-portée derrière le Ghast
            support_distance = self_range * 0.5  # 50% de la portée d'attaque

            # Calculer la direction opposée au bastion ennemi
            ennemy_bastion = self.get_ennemy_bastion(self_team)
            ennemy_bastion_pos = esper.component_for_entity(ennemy_bastion, Position)

            dx = ghast_pos.x - ennemy_bastion_pos.x
            dy = ghast_pos.y - ennemy_bastion_pos.y
            dist = (dx**2 + dy**2) ** 0.5

            if dist > 0:
                # Position de support derrière le Ghast par rapport à l'ennemi
                support_x = ghast_pos.x + (dx / dist) * support_distance
                support_y = ghast_pos.y + (dy / dist) * support_distance
                support_pos = Position(support_x, support_y)

                # Vérifier l'accessibilité et trouver un chemin sûr
                safe_support_pos = self.find_path_around_obstacles(self_pos, support_pos, 0)
                self.move_towards(self_pos, safe_support_pos, self_speed)
            else:
                # Position de fallback : cercle autour du Ghast
                self.move_towards(self_pos, ghast_pos, self_speed)

        # 5. Fallback : comportement d'attaque normal
        else:
            self.attack_behavior(self_ent, self_team, self_pos, self_vel)

#-----------------------------------------------------------
#                   boucle principale
#-----------------------------------------------------------

    def process_entity(self, ent: int, dt: float, pos: Position, vel: Velocity):
        if esper.has_component(ent, Ai_flag):
            ai_component = esper.component_for_entity(ent, Ai_flag)
            if ai_component.ai_controlled:
                team = esper.component_for_entity(ent, Team)
                team = team.team_id
                if self.is_unit_threatened(ent):
                    # Si en danger, adopter un comportement de fuite
                    self.coward_behavior(ent, team, pos, vel)
                elif len(self.get_units(EntityType.GHAST)[team-1]) != 0:
                    self.support_behavior(ent, team, pos, vel)
                else:
                    self.attack_behavior(ent, team, pos, vel)
