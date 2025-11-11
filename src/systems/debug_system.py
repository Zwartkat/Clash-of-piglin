import esper
import pygame
from systems.pathfinding_system import PATHFINDING_SYSTEM_INSTANCE
from core.game.camera import CAMERA


class DebugRenderSystem(esper.Processor):
    """
    Use to display debug information on screen when pathfinding debug mode is active.

    Improved path visualization:
    - Shows only current and next few waypoints
    - Refreshes paths every 3 seconds
    - Updates display when units reach waypoints
    """

    def __init__(self, screen: pygame.Surface, pathfinding_system=None):
        super().__init__()
        self.screen = screen
        self.font = pygame.font.Font(None, 20)
        self.pathfinding_system = pathfinding_system

        # Timer pour redessin périodique des chemins
        self.path_refresh_timer = 0.0
        self.path_refresh_interval = (
            3.0  # Redessiner toutes les 3 secondes (configurable)
        )

        # Cache des chemins actifs avec timestamps
        self.active_paths = {}  # entity_id -> {path, current_waypoint, last_update}

        # Paramètres d'affichage configurables
        self.max_visible_waypoints = 4  # Nombre max de waypoints à afficher
        self.show_entity_trail = (
            True  # Afficher la ligne directe vers le prochain waypoint
        )

        # Couleurs du debug pathfinding
        self.current_color = (0, 255, 255)  # Cyan pour segment actuel
        self.next_color = (100, 200, 255)  # Bleu clair pour prochains segments
        self.waypoint_color = (255, 255, 0)  # Jaune pour waypoints
        self.target_color = (255, 100, 100)  # Rouge pour cible actuelle
        self.destination_color = (100, 255, 100)  # Vert pour destination finale
        self.trail_color = (255, 0, 255)  # Magenta pour ligne directe

    def configure_path_display(
        self, refresh_interval=None, max_waypoints=None, show_trail=None
    ):
        """Configurer les paramètres d'affichage des chemins en temps réel."""
        if refresh_interval is not None:
            self.path_refresh_interval = max(0.5, refresh_interval)  # Minimum 0.5s
            print(f"[DEBUG] Intervalle de refresh: {self.path_refresh_interval}s")

        if max_waypoints is not None:
            self.max_visible_waypoints = max(2, min(10, max_waypoints))  # Entre 2 et 10
            print(f"[DEBUG] Waypoints visibles: {self.max_visible_waypoints}")

        if show_trail is not None:
            self.show_entity_trail = show_trail
            print(f"[DEBUG] Affichage trail: {'ON' if show_trail else 'OFF'}")

    def process(self, dt):
        # Utiliser la référence directe ou le global en fallback
        pathfinder = self.pathfinding_system or PATHFINDING_SYSTEM_INSTANCE

        if not pathfinder or not pathfinder.debug_mode:
            return

        # Mettre à jour le timer de refresh
        self.path_refresh_timer += dt
        should_refresh_paths = self.path_refresh_timer >= self.path_refresh_interval

        if should_refresh_paths:
            self.path_refresh_timer = 0.0
            print(
                f"[DEBUG] Refresh périodique des chemins (toutes les {self.path_refresh_interval}s)"
            )

        # Dessiner les zones de lave (non-walkable)
        self._draw_terrain_debug(pathfinder)

        # Mettre à jour et dessiner les chemins avec la nouvelle logique
        self._update_and_draw_paths(pathfinder, should_refresh_paths)

        # Dessiner les textes de debug
        self._draw_debug_texts(pathfinder)

        # Afficher des informations de debug générales en haut
        self._draw_debug_info(pathfinder)

    def _update_and_draw_paths(self, pathfinder, force_refresh=False):
        """Mettre à jour et dessiner les chemins avec logique intelligente."""
        import esper
        from components.ai import PathRequest
        from components.base.position import Position

        # Récupérer les entités avec pathfinding actif
        current_entities = set()

        for entity, (path_request, position) in esper.get_components(
            PathRequest, Position
        ):
            if path_request.path and len(path_request.path) > 0:
                current_entities.add(entity)

                # Vérifier si l'entité a atteint un nouveau waypoint
                current_index = getattr(path_request, "current_index", 0)

                # Si nouvel index ou refresh forcé, mettre à jour le cache
                if (
                    entity not in self.active_paths
                    or self.active_paths[entity].get("current_index", 0)
                    != current_index
                    or force_refresh
                ):

                    self._update_path_cache(
                        entity, path_request, position, current_index
                    )

                # Dessiner le chemin pour cette entité
                self._draw_entity_path(entity, position)

        # Nettoyer les entités qui n'ont plus de chemin actif
        entities_to_remove = set(self.active_paths.keys()) - current_entities
        for entity_id in entities_to_remove:
            del self.active_paths[entity_id]
            if force_refresh:
                print(f"[DEBUG] Chemin terminé pour entité {entity_id}")

    def _update_path_cache(self, entity_id, path_request, position, current_index):
        """Mettre à jour le cache du chemin pour une entité."""
        if not path_request.path:
            return

        # Calculer quels waypoints afficher
        total_waypoints = len(path_request.path)
        start_index = max(0, current_index - 1)  # Inclure le waypoint précédent
        end_index = min(total_waypoints, current_index + self.max_visible_waypoints)

        visible_waypoints = path_request.path[start_index:end_index]

        # Mettre à jour le cache
        self.active_paths[entity_id] = {
            "visible_waypoints": visible_waypoints,
            "current_index": current_index,
            "total_waypoints": total_waypoints,
            "entity_position": (position.x, position.y),
            "last_update": pygame.time.get_ticks(),
        }

        print(
            f"[DEBUG] Entité {entity_id}: affichage waypoints {start_index}-{end_index-1} sur {total_waypoints}"
        )

    def _draw_entity_path(self, entity_id, current_position):
        """Dessiner le chemin pour une entité spécifique."""
        if entity_id not in self.active_paths:
            return

        path_data = self.active_paths[entity_id]
        visible_waypoints = path_data["visible_waypoints"]
        current_index = path_data["current_index"]

        if len(visible_waypoints) < 2:
            return

        zoom = CAMERA.zoom_factor

        # Dessiner les segments du chemin
        for i in range(len(visible_waypoints) - 1):
            start_waypoint = visible_waypoints[i]
            end_waypoint = visible_waypoints[i + 1]

            # Appliquer la transformation de caméra
            start_camera = CAMERA.apply(start_waypoint.x, start_waypoint.y)
            end_camera = CAMERA.apply(end_waypoint.x, end_waypoint.y)

            # Choisir la couleur selon la position dans le chemin
            if i == 0:
                # Segment actuel (du joueur au prochain waypoint)
                color = self.current_color
                thickness = max(2, int(4 * zoom))
            else:
                # Segments suivants
                color = self.next_color
                thickness = max(1, int(2 * zoom))

            try:
                pygame.draw.line(
                    self.screen,
                    color,
                    (int(start_camera[0]), int(start_camera[1])),
                    (int(end_camera[0]), int(end_camera[1])),
                    thickness,
                )
            except (ValueError, TypeError):
                continue

        # Dessiner les waypoints
        for i, waypoint in enumerate(visible_waypoints):
            try:
                waypoint_camera = CAMERA.apply(waypoint.x, waypoint.y)

                # Taille du cercle selon l'importance
                if i == 0:
                    # Prochain waypoint cible
                    radius = max(3, int(6 * zoom))
                    color = self.target_color
                elif i == len(visible_waypoints) - 1:
                    # Destination finale visible
                    radius = max(2, int(5 * zoom))
                    color = self.destination_color
                else:
                    # Waypoints intermédiaires
                    radius = max(1, int(3 * zoom))
                    color = self.waypoint_color

                pygame.draw.circle(
                    self.screen,
                    color,
                    (int(waypoint_camera[0]), int(waypoint_camera[1])),
                    radius,
                )

                # Ajouter un contour pour plus de visibilité
                pygame.draw.circle(
                    self.screen,
                    (0, 0, 0),
                    (int(waypoint_camera[0]), int(waypoint_camera[1])),
                    radius + 1,
                    1,
                )
            except (ValueError, TypeError):
                continue

        # Ligne directe de l'entité vers le prochain waypoint
        if visible_waypoints and self.show_entity_trail:
            next_waypoint = visible_waypoints[0]
            entity_camera = CAMERA.apply(current_position.x, current_position.y)
            waypoint_camera = CAMERA.apply(next_waypoint.x, next_waypoint.y)

            try:
                pygame.draw.line(
                    self.screen,
                    self.trail_color,
                    (int(entity_camera[0]), int(entity_camera[1])),
                    (int(waypoint_camera[0]), int(waypoint_camera[1])),
                    max(1, int(2 * zoom)),
                )
            except (ValueError, TypeError):
                pass

    def _draw_debug_texts(self, pathfinder):
        """Dessiner les textes de debug."""
        debug_y_offset = (
            80  # Commencer plus bas pour éviter de couvrir l'indicateur principal
        )

        for i, text_info in enumerate(pathfinder.debug_texts):
            try:
                if len(text_info) >= 3:
                    text, position, color = text_info[:3]
                    text_surface = self.font.render(str(text), True, color)

                    # Positionner les textes de debug en colonne à gauche pour éviter l'encombrement
                    if any(
                        keyword in str(text)
                        for keyword in ["Path found", "FAILED", "Entity", "iterations"]
                    ):
                        self.screen.blit(text_surface, (10, debug_y_offset + i * 20))
                    else:
                        # Textes liés aux positions (garder leur position originale)
                        self.screen.blit(
                            text_surface, (int(position[0]) + 5, int(position[1]) - 25)
                        )
            except (ValueError, TypeError):
                continue

    def _draw_debug_info(self, pathfinder):
        """Afficher les informations générales de debug."""
        debug_info = [
            f"DEBUG MODE ACTIVE (F3 to toggle)",
            f"Active paths: {len(self.active_paths)}",
            f"Path refresh: {self.path_refresh_timer:.1f}s / {self.path_refresh_interval}s",
            f"Max waypoints shown: {self.max_visible_waypoints}",
            f"Debug messages: {len([t for t in pathfinder.debug_texts if len(t) >= 4])}",
            f"Terrain map size: {len(pathfinder.terrain_map)} tiles",
        ]

        for i, info in enumerate(debug_info):
            color = (255, 255, 0) if i == 0 else (200, 200, 200)
            text_surface = self.font.render(info, True, color)
            self.screen.blit(text_surface, (10, 10 + i * 20))

    def _draw_terrain_debug(self, pathfinder):
        """Dessine des overlays pour montrer les zones non-walkable."""
        tile_size = pathfinder.tile_size

        # Debug info seulement au début
        if not hasattr(self, "_debug_printed"):
            print(
                f"DEBUG: Terrain map a {len(pathfinder.terrain_map)} cases, tile_size={tile_size}"
            )
            lava_positions = [
                (x, y)
                for (x, y), terrain_type in pathfinder.terrain_map.items()
                if terrain_type == "LAVA"
            ]
            print(
                f"DEBUG: {len(lava_positions)} zones de lave aux positions (premières): {lava_positions[:10]}"
            )
            self._debug_printed = True

        # Parcourir la carte terrain et marquer les zones de lave
        for (x, y), terrain_type in pathfinder.terrain_map.items():
            if terrain_type == "LAVA":
                # Calculer les coordonnées pixel de base
                pixel_x = x * tile_size
                pixel_y = y * tile_size

                # Appliquer la transformation de caméra
                if CAMERA.is_visible(pixel_x, pixel_y, tile_size, tile_size):
                    camera_pos = CAMERA.apply(pixel_x, pixel_y)
                    zoom = CAMERA.zoom_factor
                    scaled_tile_size = int(tile_size * zoom)

                    # Debug: afficher quelques positions avec caméra
                    if not hasattr(self, "_lava_debug_done"):
                        # print(
                        #    f"DEBUG LAVA avec caméra: ({x},{y}) -> base({pixel_x},{pixel_y}) -> caméra({camera_pos[0]},{camera_pos[1]})"
                        # )
                        if x == 7 and y == 3:  # Premier point de lave
                            self._lava_debug_done = True

                    # Créer une surface transparente avec zoom
                    overlay = pygame.Surface(
                        (scaled_tile_size, scaled_tile_size), pygame.SRCALPHA
                    )
                    overlay.fill((255, 0, 0, 80))  # Rouge avec alpha
                    self.screen.blit(overlay, camera_pos)

                    # Dessiner un contour rouge avec zoom
                    pygame.draw.rect(
                        self.screen,
                        (255, 0, 0),
                        (
                            camera_pos[0],
                            camera_pos[1],
                            scaled_tile_size,
                            scaled_tile_size,
                        ),
                        2,
                    )
