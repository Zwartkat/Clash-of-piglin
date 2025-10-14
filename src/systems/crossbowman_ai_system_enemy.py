# Priorité des cibles
import math
import esper
from components.ai import AIMemory, AIState, AIStateType, PathRequest
from components.attack import Attack
from components.health import Health
from components.position import Position
from components.target import Target
from components.team import Team
from components.velocity import Velocity
from enums.entity_type import EntityType
from enums.case_type import CaseType


TARGET_PRIORITY = {"GHAST": 4, "CROSSBOWMAN": 3, "BRUTE": 2, "BASTION": 1}


class CrossbowmanAISystemEnemy(esper.Processor):
    def __init__(
        self, targeting_system, movement_system, arrow_system, pathfinding_system
    ):
        super().__init__()
        self.targeting_system = targeting_system
        self.movement_system = movement_system
        self.arrow_system = arrow_system
        self.pathfinding_system = pathfinding_system

    def process(self, dt):
        # D'abord, trouver tous les CROSSBOWMAN de l'équipe 2 et ajouter les composants AI s'ils manquent
        for ent, (team, entity_type, pos, attack, health) in esper.get_components(
            Team, EntityType, Position, Attack, Health
        ):
            if team.team_id != 2 or entity_type != EntityType.CROSSBOWMAN:
                continue

            # Vérifier et ajouter les composants AI manquants
            if not esper.has_component(ent, AIState):
                esper.add_component(ent, AIState())
                print(f"[IA] CROSSBOWMAN {ent} IA activée")
            if not esper.has_component(ent, AIMemory):
                esper.add_component(ent, AIMemory())
            if not esper.has_component(ent, PathRequest):
                esper.add_component(ent, PathRequest())

        # Maintenant traiter toutes les unités avec les composants AI
        for ent, (
            team,
            entity_type,
            pos,
            attack,
            health,
            ai_state,
            ai_mem,
        ) in esper.get_components(
            Team, EntityType, Position, Attack, Health, AIState, AIMemory
        ):
            if team.team_id != 2 or entity_type != EntityType.CROSSBOWMAN:
                continue

            # 1. Analyser la situation sur le terrain
            ally_brutes = self._get_ally_brutes(ent, pos, team.team_id)
            visible_enemies = self._get_visible_enemies(ent, pos, attack, team.team_id)

            # 2. Logique principale basée sur la présence de BRUTEs
            if ally_brutes:  # Des BRUTEs alliées sont présentes
                self._handle_brute_coordination(
                    ent, pos, ai_state, ally_brutes, visible_enemies, attack
                )
            else:  # Aucune BRUTE alliée
                self._handle_no_brute_behavior(
                    ent, pos, ai_state, team.team_id, visible_enemies, attack
                )

    def _get_ally_brutes(self, ent, pos, team_id):
        """Trouve toutes les BRUTEs alliées avec leurs statuts de combat"""
        brutes = []
        for brute_ent, (brute_team, brute_type, brute_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if (
                brute_ent == ent
                or brute_team.team_id != team_id
                or brute_type != EntityType.BRUTE
            ):
                continue

            # Vérifier si la BRUTE est en combat
            in_combat = esper.has_component(brute_ent, Target)
            enemies_nearby = self._count_enemies_near_position(brute_pos, team_id, 100)

            brutes.append(
                {
                    "id": brute_ent,
                    "pos": brute_pos,
                    "distance": self._distance(pos, brute_pos),
                    "in_combat": in_combat,
                    "enemies_nearby": enemies_nearby,
                }
            )

        return sorted(brutes, key=lambda x: x["distance"])  # Trier par distance

    def _handle_brute_coordination(
        self, ent, pos, ai_state, ally_brutes, visible_enemies, attack
    ):
        """Gère le comportement quand des BRUTEs sont présentes"""
        # Priorité 1: Aider les BRUTEs en combat
        brutes_in_combat = [
            b for b in ally_brutes if b["in_combat"] or b["enemies_nearby"] > 0
        ]

        if brutes_in_combat:
            # Trouver la BRUTE qui a besoin d'aide (ratio ennemis/alliés le plus élevé)
            best_brute = self._select_brute_to_help(ent, pos, brutes_in_combat)

            if best_brute:
                # Aller derrière cette BRUTE pour l'aider
                support_pos = self._get_support_position_behind_brute(
                    pos, best_brute["pos"]
                )
                dist_to_support = self._distance(pos, support_pos)

                if dist_to_support > 30:
                    ai_state.state = AIStateType.SUPPORTING
                    self._move_to(ent, pos, (support_pos.x, support_pos.y))
                    print(
                        f"[IA] CROSSBOWMAN {ent} se dirige vers BRUTE {best_brute['id']} en combat"
                    )
                else:
                    # En position, attaquer les ennemis
                    ai_state.state = AIStateType.ATTACKING
                    self._attack_nearest_enemy(ent, visible_enemies, attack)
                    print(f"[IA] CROSSBOWMAN {ent} soutient BRUTE {best_brute['id']}")
                return

        # Priorité 2: Si aucune BRUTE en combat, aller derrière la plus proche
        if ally_brutes:
            closest_brute = ally_brutes[0]  # Déjà triée par distance
            support_pos = self._get_support_position_behind_brute(
                pos, closest_brute["pos"]
            )
            dist_to_support = self._distance(pos, support_pos)

            if dist_to_support > 30:
                ai_state.state = AIStateType.SUPPORTING
                self._move_to(ent, pos, (support_pos.x, support_pos.y))
                print(f"[IA] CROSSBOWMAN {ent} rejoint BRUTE {closest_brute['id']}")
            else:
                ai_state.state = AIStateType.IDLE
                self._stop_movement(ent)
                print(f"[IA] CROSSBOWMAN {ent} en position derrière BRUTE")

    def _handle_no_brute_behavior(
        self, ent, pos, ai_state, team_id, visible_enemies, attack
    ):
        """Gère le comportement quand aucune BRUTE n'est présente"""
        ally_crossbowmen = self._get_ally_crossbowmen(ent, pos, team_id)
        enemy_power = self._calculate_enemy_power_global(team_id)
        ally_power = len(ally_crossbowmen) + 1  # +1 pour soi-même

        # Vérifier s'il y a des ennemis sur le terrain
        enemies_exist = self._check_enemies_exist(team_id)

        if enemy_power > ally_power:
            # Puissance ennemie supérieure -> retour au bastion
            ai_state.state = AIStateType.RETREATING
            base_pos = self._get_base_position(team_id)
            if self._distance(pos, base_pos) > 80:
                self._move_to(ent, pos, (base_pos.x, base_pos.y))
                print(
                    f"[IA] CROSSBOWMAN {ent} retourne au bastion (ennemis plus forts)"
                )
            else:
                ai_state.state = AIStateType.IDLE
                self._stop_movement(ent)
                print(f"[IA] CROSSBOWMAN {ent} attend au bastion")

        elif enemies_exist:
            # Puissance suffisante -> attaque en groupe
            if visible_enemies:
                ai_state.state = AIStateType.ATTACKING
                self._attack_with_group_tactics(
                    ent, pos, visible_enemies, attack, ally_crossbowmen
                )
            else:
                # Chercher des ennemis avec les autres arbalétriers
                ai_state.state = AIStateType.SUPPORTING
                self._move_with_group(ent, pos, ally_crossbowmen, team_id)

        else:
            # Plus d'ennemis -> attaquer le bastion ennemi
            ai_state.state = AIStateType.ATTACKING
            enemy_bastion_pos = self._find_enemy_bastion(team_id)
            if enemy_bastion_pos:
                self._move_to(ent, pos, (enemy_bastion_pos.x, enemy_bastion_pos.y))
                print(f"[IA] CROSSBOWMAN {ent} attaque le bastion ennemi")

    def _get_visible_enemies(self, ent, pos, attack, team_id):
        """Retourne une liste des ennemis visibles à portée"""
        visible_enemies = []

        for target_ent, (target_pos, target_team, target_type) in esper.get_components(
            Position, Team, EntityType
        ):
            # Skip allies and self
            if target_ent == ent or target_team.team_id == team_id:
                continue

            # Must be alive
            if not esper.has_component(target_ent, Health):
                continue

            target_health = esper.component_for_entity(target_ent, Health)
            if target_health.remaining <= 0:
                continue

            # Check if in range (plus large que la portée d'attaque pour détecter à l'avance)
            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            distance = (dx**2 + dy**2) ** 0.5
            if distance <= attack.range * 1.5:  # Zone de détection plus large
                visible_enemies.append((target_ent, target_pos, target_type))

        return visible_enemies

    def _select_priority_target(self, visible_enemies):
        # visible_enemies: list of (entity_id, Position, EntityType)
        if visible_enemies is None or len(visible_enemies) == 0:
            return None, None, None
        best_score = -1
        best_id = None
        best_pos = None
        best_type = None
        for eid, pos, ut in visible_enemies:
            score = TARGET_PRIORITY.get(ut.name, 0)
            if score > best_score:
                best_score = score
                best_id = eid
                best_pos = pos
                best_type = ut
        return best_id, best_pos, best_type

    def _distance(self, pos1, pos2):
        return math.hypot(pos1.x - pos2.x, pos1.y - pos2.y)

    def _get_retreat_position(self, pos, target_pos):
        # Reculer derrière le vecteur opposé à la cible
        dx = pos.x - target_pos.x
        dy = pos.y - target_pos.y
        norm = math.hypot(dx, dy)
        if norm == 0:
            return (pos.x, pos.y)
        retreat_x = pos.x + dx / norm * 60.0  # Distance de retraite
        retreat_y = pos.y + dy / norm * 60.0
        return (retreat_x, retreat_y)

    def _get_approach_position(self, pos, target_pos, desired_distance):
        # Se rapprocher jusqu'à une distance désirée
        dx = target_pos.x - pos.x
        dy = target_pos.y - pos.y
        norm = math.hypot(dx, dy)
        if norm == 0:
            return (pos.x, pos.y)
        approach_x = target_pos.x - (dx / norm) * desired_distance
        approach_y = target_pos.y - (dy / norm) * desired_distance
        return (approach_x, approach_y)

    def _move_to(self, ent, current_pos, destination):
        """Déplace l'entité vers une destination avec mouvement intelligent"""
        # Calculer la distance à la destination
        dx = destination[0] - current_pos.x
        dy = destination[1] - current_pos.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 30:  # Assez proche, arrêter
            self._stop_movement(ent)
            return

        # TEMPORAIRE: Utiliser mouvement direct pour corriger le problème immédiat
        # TODO: Réactiver pathfinding A* quand le système de carte sera corrigé
        self._move_direct_safe(ent, current_pos, destination)

    def _has_lava_on_path(self, start_pos, end_pos):
        """Vérifie rapidement s'il y a de la lave sur le chemin direct"""
        # Échantillonner quelques points sur le chemin
        steps = 5
        for i in range(1, steps):
            t = i / steps
            x = start_pos.x + t * (end_pos[0] - start_pos.x)
            y = start_pos.y + t * (end_pos[1] - start_pos.y)

            grid_x = int(x // 24)
            grid_y = int(y // 24)

            if (
                self.pathfinding_system.terrain_map.get((grid_x, grid_y))
                == CaseType.LAVA
            ):
                return True
        return False

    def _move_with_pathfinding(self, ent, current_pos, destination):
        """Utilise le pathfinding A* pour contourner les obstacles"""
        path_req = esper.component_for_entity(ent, PathRequest)

        # Demander un nouveau chemin si nécessaire
        dest_tuple = (destination[0], destination[1])
        if not path_req.path or path_req.destination != dest_tuple:
            path_req.destination = dest_tuple
            path_req.path = None
            path_req.current_index = 0
            print(
                f"[IA] Demande nouveau chemin pour {ent}: ({current_pos.x},{current_pos.y}) -> {dest_tuple}"
            )

            # En attendant le pathfinding, ne pas bouger
            self._stop_movement(ent)
            return

        # Suivre le chemin calculé
        if path_req.path and len(path_req.path) > 0:
            if path_req.current_index < len(path_req.path):
                next_waypoint = path_req.path[path_req.current_index]

                # Distance au waypoint
                dx = next_waypoint.x - current_pos.x
                dy = next_waypoint.y - current_pos.y
                dist = math.sqrt(dx * dx + dy * dy)

                print(
                    f"[IA] {ent} suit chemin waypoint {path_req.current_index}/{len(path_req.path)} distance: {dist:.1f}"
                )

                if dist < 20:  # Proche du waypoint
                    path_req.current_index += 1
                    print(f"[IA] {ent} waypoint {path_req.current_index-1} atteint")
                    if path_req.current_index >= len(path_req.path):
                        # Chemin terminé
                        print(f"[IA] {ent} chemin A* terminé")
                        self._stop_movement(ent)
                        path_req.path = None  # Reset pour éviter la boucle
                        return

                # Se déplacer vers le waypoint
                self._set_velocity(ent, dx, dy)
            else:
                self._stop_movement(ent)
        else:
            # Fallback si pas de chemin trouvé après 3 secondes
            if not hasattr(path_req, "wait_frames"):
                path_req.wait_frames = 0

            path_req.wait_frames += 1
            if path_req.wait_frames > 180:  # 3 secondes à 60 FPS
                print(f"[IA] {ent} timeout pathfinding A*, fallback mouvement direct")
                self._move_direct_safe(ent, current_pos, destination)
            else:
                self._stop_movement(ent)

    def _move_direct_safe(self, ent, current_pos, destination):
        """Mouvement direct avec évitement basique de lave"""
        dx = destination[0] - current_pos.x
        dy = destination[1] - current_pos.y

        # Évitement basique de la lave - si on va vers une case de lave, contourner
        next_x = current_pos.x + (dx / abs(dx) if dx != 0 else 0) * 24
        next_y = current_pos.y + (dy / abs(dy) if dy != 0 else 0) * 24

        grid_x = int(next_x // 24)
        grid_y = int(next_y // 24)

        # Vérifier si la prochaine case est de la lave
        if (
            hasattr(self, "pathfinding_system")
            and self.pathfinding_system.terrain_map.get((grid_x, grid_y))
            == CaseType.LAVA
        ):
            # Contourner la lave en allant perpendiculairement
            if abs(dx) > abs(dy):
                # Aller verticalement pour contourner
                bypass_dx = dx * 0.3  # Avancer un peu
                bypass_dy = 48 if dy >= 0 else -48  # Contourner verticalement
            else:
                # Aller horizontalement pour contourner
                bypass_dx = 48 if dx >= 0 else -48  # Contourner horizontalement
                bypass_dy = dy * 0.3  # Avancer un peu

            self._set_velocity(ent, bypass_dx, bypass_dy)
            print(f"[IA] CROSSBOWMAN {ent} contourne la lave")

        # Vérifier collision avec BRUTEs statiques
        elif self._would_collide_with_static_brute(current_pos, destination):
            # Contourner la BRUTE
            self._move_around_brute(ent, current_pos, destination)
        else:
            # Mouvement direct normal
            self._set_velocity(ent, dx, dy)

    def _move_around_obstacle(self, ent, current_pos, destination):
        """Mouvement de contournement simple"""
        dx = destination[0] - current_pos.x
        dy = destination[1] - current_pos.y

        # Essayer un mouvement perpendiculaire pour contourner
        if abs(dx) > abs(dy):
            # Obstacle horizontal, essayer de contourner verticalement
            offset_y = 48 if dy >= 0 else -48
            test_x = current_pos.x
            test_y = current_pos.y + offset_y
        else:
            # Obstacle vertical, essayer de contourner horizontalement
            offset_x = 48 if dx >= 0 else -48
            test_x = current_pos.x + offset_x
            test_y = current_pos.y

        # Vérifier si la position de contournement est sûre
        grid_x = int(test_x // 24)
        grid_y = int(test_y // 24)

        if self.pathfinding_system.terrain_map.get((grid_x, grid_y)) != CaseType.LAVA:
            self._set_velocity(ent, test_x - current_pos.x, test_y - current_pos.y)
        else:
            # Si le contournement échoue, essayer l'autre direction
            if abs(dx) > abs(dy):
                offset_y = -offset_y
                test_y = current_pos.y + offset_y
            else:
                offset_x = -offset_x
                test_x = current_pos.x + offset_x

            self._set_velocity(ent, test_x - current_pos.x, test_y - current_pos.y)

    def _set_velocity(self, ent, dx, dy):
        """Définit la vélocité de l'entité"""
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
        else:
            vel = Velocity(0, 0)
            esper.add_component(ent, vel)

        vel.x = dx
        vel.y = dy

    def _would_collide_with_static_brute(self, current_pos, destination):
        """Vérifie si le chemin vers la destination va percuter une BRUTE statique"""
        for brute_ent, (
            brute_team,
            brute_type,
            brute_pos,
            brute_vel,
        ) in esper.get_components(Team, EntityType, Position, Velocity):
            if (
                brute_type != EntityType.BRUTE
                or not hasattr(brute_team, "team_id")
                or brute_team.team_id != 2
            ):
                continue

            # Vérifier si la BRUTE est statique
            if abs(brute_vel.x) < 0.1 and abs(brute_vel.y) < 0.1:
                # Calculer si le chemin passe près de cette BRUTE
                dist_to_path = self._point_to_line_distance(
                    brute_pos, current_pos, Position(destination[0], destination[1])
                )
                if dist_to_path < 30:  # Trop proche du chemin
                    return True
        return False

    def _point_to_line_distance(self, point, line_start, line_end):
        """Calcule la distance d'un point à une ligne"""
        # Distance point-ligne simplifiée
        x0, y0 = point.x, point.y
        x1, y1 = line_start.x, line_start.y
        x2, y2 = line_end.x, line_end.y

        # Si la ligne est un point
        if x1 == x2 and y1 == y2:
            return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

        # Distance point-ligne
        num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        den = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        return num / den if den > 0 else float("inf")

    def _move_around_brute(self, ent, current_pos, destination):
        """Contourne une BRUTE pour aller vers la destination"""
        # Trouver la BRUTE la plus proche qui bloque le chemin
        closest_brute_pos = None
        min_dist = float("inf")

        for brute_ent, (brute_team, brute_type, brute_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if (
                brute_type != EntityType.BRUTE
                or not hasattr(brute_team, "team_id")
                or brute_team.team_id != 2
            ):
                continue

            dist = self._distance(current_pos, brute_pos)
            if dist < min_dist and dist < 50:  # Proche et potentiellement bloquante
                min_dist = dist
                closest_brute_pos = brute_pos

        if closest_brute_pos:
            # Calculer une position de contournement
            brute_to_dest_x = destination[0] - closest_brute_pos.x
            brute_to_dest_y = destination[1] - closest_brute_pos.y

            # Position de contournement sur le côté
            if abs(brute_to_dest_x) > abs(brute_to_dest_y):
                # Contourner verticalement
                offset_y = 48 if brute_to_dest_y >= 0 else -48
                bypass_x = closest_brute_pos.x
                bypass_y = closest_brute_pos.y + offset_y
            else:
                # Contourner horizontalement
                offset_x = 48 if brute_to_dest_x >= 0 else -48
                bypass_x = closest_brute_pos.x + offset_x
                bypass_y = closest_brute_pos.y

            # Se diriger vers la position de contournement
            dx = bypass_x - current_pos.x
            dy = bypass_y - current_pos.y
            self._set_velocity(ent, dx, dy)
        else:
            # Pas de BRUTE à contourner, mouvement direct
            dx = destination[0] - current_pos.x
            dy = destination[1] - current_pos.y
            self._set_velocity(ent, dx, dy)

    def _stop_movement(self, ent):
        """Arrête le mouvement de l'entité"""
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
            vel.x = 0
            vel.y = 0

    def _move_direct(self, ent, current_pos, destination):
        """Mouvement direct vers la destination (fallback simple)"""
        dx = destination[0] - current_pos.x
        dy = destination[1] - current_pos.y
        distance = (dx**2 + dy**2) ** 0.5

        # Si on est proche de la destination, arrêter
        if distance < 20:
            self._stop_movement(ent)
            return

        # Vérifier qu'on ne va pas percuter une BRUTE statique
        target_pos = Position(destination[0], destination[1])
        if self._would_collide_with_brute(ent, current_pos, target_pos):
            # Si collision imminente, arrêter et attendre
            self._stop_movement(ent)
            return

        # Configurer la vélocité pour mouvement direct
        if esper.has_component(ent, Velocity):
            vel = esper.component_for_entity(ent, Velocity)
        else:
            vel = Velocity(0, 0)
            esper.add_component(ent, vel)

        # MovementSystem normalisera automatiquement
        vel.x = dx  # Direction brute
        vel.y = dy  # Direction brute

    def _would_collide_with_brute(self, ent, current_pos, target_pos):
        """Vérifie si le mouvement vers target_pos va percuter une BRUTE statique"""
        # Chercher les BRUTEs alliées proches
        try:
            for brute_ent, (brute_team, brute_type, brute_pos) in esper.get_components(
                Team, EntityType, Position
            ):
                if (
                    brute_ent == ent
                    or brute_type != EntityType.BRUTE
                    or brute_team.team_id != 2
                ):
                    continue

                # Vérifier si on a une vélocité pour cette BRUTE
                brute_moving = False
                if esper.has_component(brute_ent, Velocity):
                    brute_vel = esper.component_for_entity(brute_ent, Velocity)
                    brute_moving = abs(brute_vel.x) > 0.5 or abs(brute_vel.y) > 0.5

                # Si la BRUTE est statique ET qu'on va trop près d'elle
                if not brute_moving:
                    dist_to_brute = self._distance(target_pos, brute_pos)
                    if dist_to_brute < 35:  # Distance de sécurité
                        return True
        except Exception as e:
            # En cas d'erreur, continuer sans bloquer
            pass

        return False

    def _get_support_position_behind_brute(self, crossbow_pos, brute_pos):
        """Calcule une position de soutien derrière une BRUTE (pas trop proche)"""
        # Trouver la direction générale des ennemis pour se positionner du bon côté
        enemy_center = self._get_enemy_center_mass(2)  # team_id = 2

        if enemy_center:
            # Se positionner du côté opposé aux ennemis par rapport à la BRUTE
            brute_to_enemy_x = enemy_center.x - brute_pos.x
            brute_to_enemy_y = enemy_center.y - brute_pos.y

            # Normaliser la direction
            norm = math.sqrt(brute_to_enemy_x**2 + brute_to_enemy_y**2)
            if norm > 0:
                # Position derrière la BRUTE (côté opposé aux ennemis)
                offset_x = -(brute_to_enemy_x / norm) * 48  # 2 cases derrière
                offset_y = -(brute_to_enemy_y / norm) * 48

                support_x = brute_pos.x + offset_x
                support_y = brute_pos.y + offset_y

                return Position(support_x, support_y)

        # Position par défaut : légèrement derrière et sur le côté
        offset_x = -36 if brute_pos.x > crossbow_pos.x else 36
        offset_y = -12
        return Position(brute_pos.x + offset_x, brute_pos.y + offset_y)

    def _get_enemy_center_mass(self, team_id):
        """Calcule le centre de masse des ennemis"""
        enemy_positions = []
        for ent, (team, pos) in esper.get_components(Team, Position):
            if hasattr(team, "team_id") and team.team_id != team_id:
                enemy_positions.append(pos)

        if not enemy_positions:
            return None

        avg_x = sum(pos.x for pos in enemy_positions) / len(enemy_positions)
        avg_y = sum(pos.y for pos in enemy_positions) / len(enemy_positions)

        return Position(avg_x, avg_y)

    def _patrol_behavior(self, ent, pos, ai_state, dt):
        """Comportement de patrouille quand aucun ennemi n'est détecté"""
        ai_state.state_timer += dt

        if ai_state.state_timer >= 3.0:
            ai_state.state_timer = 0
            import random

            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(50, 100)
            patrol_x = pos.x + math.cos(angle) * distance
            patrol_y = pos.y + math.sin(angle) * distance

            self._move_to(ent, pos, (patrol_x, patrol_y))
            print(
                f"[IA] CROSSBOWMAN {ent} patrouille vers ({patrol_x:.1f}, {patrol_y:.1f})"
            )

    def _analyze_ally_forces(self, ent, pos, team_id):
        """Analyse les forces alliées à proximité"""
        allies = {"crossbowmen": 0, "brutes": 0, "ghasts": 0, "bastions": 0}

        for ally_ent, (ally_team, ally_type, ally_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if ally_ent == ent or ally_team.team_id != team_id:
                continue

            dist = self._distance(pos, ally_pos)
            if dist <= 150:  # Rayon d'analyse tactique
                if ally_type == EntityType.CROSSBOWMAN:
                    allies["crossbowmen"] += 1
                elif ally_type == EntityType.BRUTE:
                    allies["brutes"] += 1
                elif ally_type == EntityType.GHAST:
                    allies["ghasts"] += 1
                elif ally_type == EntityType.BASTION:
                    allies["bastions"] += 1

        return allies

    def _analyze_enemy_forces(self, pos, team_id):
        """Analyse les forces ennemies à proximité"""
        enemies = {"crossbowmen": 0, "brutes": 0, "ghasts": 0, "bastions": 0}

        for enemy_ent, (enemy_team, enemy_type, enemy_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if enemy_team.team_id == team_id:
                continue

            dist = self._distance(pos, enemy_pos)
            if dist <= 200:  # Rayon d'analyse étendu pour les ennemis
                if enemy_type == EntityType.CROSSBOWMAN:
                    enemies["crossbowmen"] += 1
                elif enemy_type == EntityType.BRUTE:
                    enemies["brutes"] += 1
                elif enemy_type == EntityType.GHAST:
                    enemies["ghasts"] += 1
                elif enemy_type == EntityType.BASTION:
                    enemies["bastions"] += 1

        return enemies

    def _make_strategic_decision(
        self, ent, pos, visible_enemies, ally_forces, enemy_forces
    ):
        """Prend une décision stratégique basée sur l'analyse tactique"""
        # Priorité 1: Focus GHAST (menace critique pour le bastion)
        for enemy_id, enemy_pos, enemy_type in visible_enemies:
            if enemy_type == EntityType.GHAST:
                return "FOCUS_GHAST"

        # Calcul de la puissance relative
        ally_power = (
            ally_forces["crossbowmen"] * 2
            + ally_forces["brutes"] * 4
            + ally_forces["ghasts"] * 3
        )
        enemy_power = (
            enemy_forces["crossbowmen"] * 2
            + enemy_forces["brutes"] * 4
            + enemy_forces["ghasts"] * 3
        )

        # Priorité 2: Coordination avec les BRUTEs
        if ally_forces["brutes"] > 0:
            return "ADVANCE_WITH_BRUTE"  # Nouveau comportement coordonné

        # Priorité 3: Si pas de BRUTEs, vérifier la puissance
        if ally_power >= enemy_power:
            # Puissance suffisante pour attaquer seul
            if enemy_forces["bastions"] > 0 and ally_power > enemy_power * 1.2:
                return "ATTACK_BASTION"
            else:
                return "SOLO_ATTACK"
        else:
            # Puissance insuffisante, attendre au bastion
            return "WAIT_AT_BASE"

    def _select_strategic_target(self, visible_enemies, strategic_decision):
        """Sélectionne une cible selon la stratégie"""
        if strategic_decision == "FOCUS_GHAST":
            # Priorité absolue aux GHAST
            for enemy_id, enemy_pos, enemy_type in visible_enemies:
                if enemy_type == EntityType.GHAST:
                    return enemy_id, enemy_pos, enemy_type

        elif strategic_decision == "ATTACK_BASTION":
            # Priorité aux BASTION
            for enemy_id, enemy_pos, enemy_type in visible_enemies:
                if enemy_type == EntityType.BASTION:
                    return enemy_id, enemy_pos, enemy_type

        # Sinon, utiliser la priorité normale
        return self._select_priority_target(visible_enemies)

    def _find_combat_brute(self, ent, pos, team_id):
        """Trouve une BRUTE alliée engagée en combat"""
        for brute_ent, (brute_team, brute_type, brute_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if (
                brute_ent == ent
                or brute_team.team_id != team_id
                or brute_type != EntityType.BRUTE
            ):
                continue

            dist = self._distance(pos, brute_pos)
            if dist <= 120:  # Rayon de soutien
                # Vérifier si la BRUTE est en combat (a une cible)
                if esper.has_component(brute_ent, Target):
                    return brute_ent, brute_pos

        return None, None

    def _find_nearest_brute(self, ent, pos, team_id):
        """Trouve la BRUTE alliée la plus proche pour coordination"""
        closest_brute = None
        closest_pos = None
        min_dist = float("inf")

        for brute_ent, (brute_team, brute_type, brute_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if (
                brute_ent == ent
                or brute_team.team_id != team_id
                or brute_type != EntityType.BRUTE
            ):
                continue

            dist = self._distance(pos, brute_pos)
            if dist < min_dist and dist <= 150:  # Rayon de coordination
                min_dist = dist
                closest_brute = brute_ent
                closest_pos = brute_pos

        return closest_brute, closest_pos

    def _get_brute_advance_position(self, pos, brute_pos):
        """Calcule la position d'avancée en formation avec la BRUTE"""
        # Position légèrement derrière et sur le côté de la BRUTE
        dx = brute_pos.x - pos.x
        dy = brute_pos.y - pos.y

        if abs(dx) > abs(dy):
            # Formation horizontale
            offset_x = -24 if dx > 0 else 24
            offset_y = 0
        else:
            # Formation verticale
            offset_x = 0
            offset_y = -24 if dy > 0 else 24

        return Position(brute_pos.x + offset_x, brute_pos.y + offset_y)

    def _get_advance_direction(self, team_id):
        """Détermine la direction générale d'avancée vers l'ennemi"""
        # Trouve le centre de masse des ennemis
        enemy_positions = []
        for ent, (team, pos) in esper.get_components(Team, Position):
            if team.team_id != team_id:
                enemy_positions.append(pos)

        if not enemy_positions:
            return Position(12 * 24, 12 * 24)  # Centre de la carte par défaut

        # Centre de masse des ennemis
        avg_x = sum(pos.x for pos in enemy_positions) / len(enemy_positions)
        avg_y = sum(pos.y for pos in enemy_positions) / len(enemy_positions)

        return Position(avg_x, avg_y)

    def _defensive_behavior(self, ent, pos, ai_state):
        """Comportement défensif : rester au bastion et défendre"""
        # Position défensive proche du bastion (spawn)
        bastion_pos = Position(23 * 24, 1 * 24)  # Position du bastion équipe 2

        # Si trop loin du bastion, y retourner
        if self._distance(pos, bastion_pos) > 72:  # 3 cases
            self._move_to(ent, pos, (bastion_pos.x, bastion_pos.y))
        else:
            # Rester immobile en défense
            if esper.has_component(ent, Velocity):
                vel = esper.component_for_entity(ent, Velocity)
                vel.x = 0
                vel.y = 0

    def _get_brute_support_position(self, pos, brute_pos, brute_id):
        """Calcule la position de soutien derrière une BRUTE"""
        # Trouver l'ennemi de la BRUTE pour se positionner à l'opposé
        if esper.has_component(brute_id, Target):
            target_comp = esper.component_for_entity(brute_id, Target)
            if target_comp.target_entity_id and esper.has_component(
                target_comp.target_entity_id, Position
            ):
                enemy_pos = esper.component_for_entity(
                    target_comp.target_entity_id, Position
                )

                # Se positionner à l'opposé de l'ennemi par rapport à la BRUTE
                dx = brute_pos.x - enemy_pos.x
                dy = brute_pos.y - enemy_pos.y
                norm = math.hypot(dx, dy)
                if norm > 0:
                    support_x = brute_pos.x + (dx / norm) * 40  # 40 pixels derrière
                    support_y = brute_pos.y + (dy / norm) * 40
                    return Position(support_x, support_y)

        # Position par défaut derrière la BRUTE
        return Position(brute_pos.x - 30, brute_pos.y)

    def _get_base_position(self, team_id):
        """Trouve la position de la base (BASTION) de l'équipe"""
        for base_ent, (base_team, base_type, base_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if base_team.team_id == team_id and base_type == EntityType.BASTION:
                return base_pos

        # Position par défaut si pas de bastion
        if team_id == 1:
            return Position(100, 100)  # Coin gauche pour équipe 1
        else:
            return Position(700, 500)  # Coin droit pour équipe 2

    # === NOUVELLES MÉTHODES POUR LE COMPORTEMENT SPÉCIFIQUE ===

    def _count_enemies_near_position(self, pos, team_id, radius):
        """Compte les ennemis dans un rayon donné autour d'une position"""
        count = 0
        for enemy_ent, (enemy_team, enemy_pos) in esper.get_components(Team, Position):
            if (
                enemy_team.team_id != team_id
                and self._distance(pos, enemy_pos) <= radius
            ):
                count += 1
        return count

    def _select_brute_to_help(self, ent, pos, brutes_in_combat):
        """Sélectionne la BRUTE qui a le plus besoin d'aide"""
        best_brute = None
        max_priority = -1

        for brute in brutes_in_combat:
            # Calculer la priorité basée sur le nombre d'ennemis et la distance
            priority = (
                brute["enemies_nearby"] - brute["distance"] / 50
            )  # Plus d'ennemis = plus prioritaire, plus proche = plus prioritaire

            if priority > max_priority:
                max_priority = priority
                best_brute = brute

        return best_brute

    def _get_support_position_behind_brute(self, crossbowman_pos, brute_pos):
        """Calcule la position de soutien derrière une BRUTE"""
        # Position légèrement derrière la BRUTE (côté opposé aux ennemis)
        offset_distance = 48  # 2 cases derrière

        # Essayer de trouver les ennemis pour se positionner à l'opposé
        enemy_center = self._find_enemy_center_near_brute(brute_pos)

        if enemy_center:
            # Se positionner à l'opposé des ennemis
            dx = brute_pos.x - enemy_center.x
            dy = brute_pos.y - enemy_center.y
            norm = math.hypot(dx, dy)

            if norm > 0:
                support_x = brute_pos.x + (dx / norm) * offset_distance
                support_y = brute_pos.y + (dy / norm) * offset_distance
                return Position(support_x, support_y)

        # Position par défaut : légèrement derrière selon la direction générale
        return Position(brute_pos.x - 24, brute_pos.y)

    def _find_enemy_center_near_brute(self, brute_pos):
        """Trouve le centre des ennemis près d'une BRUTE"""
        enemy_positions = []

        for enemy_ent, (enemy_team, enemy_pos) in esper.get_components(Team, Position):
            if enemy_team.team_id != 2 and self._distance(brute_pos, enemy_pos) <= 120:
                enemy_positions.append(enemy_pos)

        if enemy_positions:
            avg_x = sum(pos.x for pos in enemy_positions) / len(enemy_positions)
            avg_y = sum(pos.y for pos in enemy_positions) / len(enemy_positions)
            return Position(avg_x, avg_y)

        return None

    def _attack_nearest_enemy(self, ent, visible_enemies, attack):
        """Attaque l'ennemi le plus proche avec gestion de la retraite"""
        if not visible_enemies:
            return

        # Trouver l'ennemi le plus proche
        closest_enemy = min(
            visible_enemies,
            key=lambda e: self._distance(
                esper.component_for_entity(ent, Position), e[1]
            ),
        )

        target_id, target_pos, target_type = closest_enemy
        current_pos = esper.component_for_entity(ent, Position)
        dist = self._distance(current_pos, target_pos)

        # Logique de combat avec retraite
        if dist < attack.range * 0.6:  # Trop proche -> reculer
            retreat_pos = self._get_retreat_position(current_pos, target_pos)
            self._move_to(ent, current_pos, retreat_pos)
            print(f"[IA] CROSSBOWMAN {ent} recule en tirant sur {target_id}")

        # Assigner la cible pour tirer
        if not esper.has_component(ent, Target):
            esper.add_component(ent, Target(target_id))
        else:
            target_comp = esper.component_for_entity(ent, Target)
            target_comp.target_entity_id = target_id

    def _get_ally_crossbowmen(self, ent, pos, team_id):
        """Trouve tous les arbalétriers alliés"""
        allies = []
        for ally_ent, (ally_team, ally_type, ally_pos) in esper.get_components(
            Team, EntityType, Position
        ):
            if (
                ally_ent != ent
                and ally_team.team_id == team_id
                and ally_type == EntityType.CROSSBOWMAN
            ):
                allies.append({"id": ally_ent, "pos": ally_pos})
        return allies

    def _calculate_enemy_power_global(self, team_id):
        """Calcule la puissance totale des ennemis sur le terrain"""
        power = 0
        for enemy_ent, (enemy_team, enemy_type) in esper.get_components(
            Team, EntityType
        ):
            if enemy_team.team_id != team_id:
                if enemy_type == EntityType.BRUTE:
                    power += 4
                elif enemy_type == EntityType.CROSSBOWMAN:
                    power += 2
                elif enemy_type == EntityType.GHAST:
                    power += 3
        return power

    def _check_enemies_exist(self, team_id):
        """Vérifie s'il y a encore des ennemis sur le terrain"""
        for enemy_ent, (enemy_team, enemy_type) in esper.get_components(
            Team, EntityType
        ):
            if enemy_team.team_id != team_id and enemy_type in [
                EntityType.BRUTE,
                EntityType.CROSSBOWMAN,
                EntityType.GHAST,
            ]:
                return True
        return False

    def _attack_with_group_tactics(
        self, ent, pos, visible_enemies, attack, ally_crossbowmen
    ):
        """Attaque avec tactiques de groupe"""
        # Prioriser les GHAST puis les autres
        priority_target = None
        for enemy_id, enemy_pos, enemy_type in visible_enemies:
            if enemy_type == EntityType.GHAST:
                priority_target = (enemy_id, enemy_pos, enemy_type)
                break

        if not priority_target:
            priority_target = visible_enemies[0] if visible_enemies else None

        if priority_target:
            target_id, target_pos, target_type = priority_target
            dist = self._distance(pos, target_pos)

            # Maintenir distance optimale et attaquer
            if dist < attack.range * 0.7:
                retreat_pos = self._get_retreat_position(pos, target_pos)
                self._move_to(ent, pos, retreat_pos)
            elif dist > attack.range * 0.9:
                approach_pos = self._get_approach_position(
                    pos, target_pos, attack.range * 0.8
                )
                self._move_to(ent, pos, approach_pos)

            # Assigner la cible
            if not esper.has_component(ent, Target):
                esper.add_component(ent, Target(target_id))
            else:
                target_comp = esper.component_for_entity(ent, Target)
                target_comp.target_entity_id = target_id

    def _move_with_group(self, ent, pos, ally_crossbowmen, team_id):
        """Se déplace en groupe pour chercher des ennemis"""
        if ally_crossbowmen:
            # Calculer le centre du groupe
            group_center_x = sum(ally["pos"].x for ally in ally_crossbowmen) / len(
                ally_crossbowmen
            )
            group_center_y = sum(ally["pos"].y for ally in ally_crossbowmen) / len(
                ally_crossbowmen
            )

            # Se diriger vers le centre du terrain pour chercher des ennemis
            map_center = Position(12 * 24, 12 * 24)  # Centre de la carte 24x24
            self._move_to(ent, pos, (map_center.x, map_center.y))
        else:
            # Seul, chercher prudemment
            enemy_base = self._find_enemy_bastion(team_id)
            if enemy_base:
                # Approcher prudemment du bastion ennemi
                approach_pos = self._get_approach_position(
                    pos, enemy_base, 120
                )  # Rester à distance
                self._move_to(ent, pos, approach_pos)

    def _find_enemy_bastion(self, team_id):
        """Trouve le bastion ennemi"""
        for bastion_ent, (
            bastion_team,
            bastion_type,
            bastion_pos,
        ) in esper.get_components(Team, EntityType, Position):
            if bastion_team.team_id != team_id and bastion_type == EntityType.BASTION:
                return bastion_pos
        return None
