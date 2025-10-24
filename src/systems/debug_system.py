import esper
import pygame
from systems.pathfinding_system import PATHFINDING_SYSTEM_INSTANCE
from core.camera import CAMERA


class DebugRenderSystem(esper.Processor):
    """
    Use to display debug information on screen when pathfinding debug mode is active.
    """

    def __init__(self, screen: pygame.Surface, pathfinding_system=None):
        super().__init__()
        self.screen = screen
        self.font = pygame.font.Font(None, 20)
        self.pathfinding_system = pathfinding_system

    def process(self, dt):
        # Utiliser la référence directe ou le global en fallback
        pathfinder = self.pathfinding_system or PATHFINDING_SYSTEM_INSTANCE

        if not pathfinder or not pathfinder.debug_mode:
            return

        # Dessiner les zones de lave (non-walkable)
        self._draw_terrain_debug(pathfinder)

        # Dessiner les lignes de debug (chemins)
        # Format: [(lines_list, entity_id), ...] où lines_list = [(start, end), ...]
        if pathfinder.debug_lines:
            print(
                f"Dessin de {len(pathfinder.debug_lines)} chemins debug"
            )  # Debug temporaire

        for lines_data, entity_id in pathfinder.debug_lines:
            print(
                f"Chemin entité {entity_id}: {len(lines_data)} segments"
            )  # Debug temporaire
            for start_pos, end_pos in lines_data:
                try:
                    # Appliquer la transformation de caméra aux positions des chemins
                    start_camera = CAMERA.apply(start_pos[0], start_pos[1])
                    end_camera = CAMERA.apply(end_pos[0], end_pos[1])
                    zoom = CAMERA.zoom_factor

                    # Dessiner une ligne entre deux points du chemin avec transformation caméra
                    pygame.draw.line(
                        self.screen,
                        (0, 255, 255),  # Cyan pour les chemins
                        (int(start_camera[0]), int(start_camera[1])),
                        (int(end_camera[0]), int(end_camera[1])),
                        max(1, int(3 * zoom)),  # Épaisseur adaptée au zoom
                    )
                    # Ajouter des points aux waypoints avec transformation caméra
                    pygame.draw.circle(
                        self.screen,
                        (255, 255, 0),  # Jaune pour les waypoints
                        (int(start_camera[0]), int(start_camera[1])),
                        max(2, int(4 * zoom)),  # Rayon adapté au zoom
                    )
                except (ValueError, TypeError):
                    continue

        # Dessiner les textes de debug
        # Format: [(text, position, color), ...] ou [(text, position, color, timeout), ...]
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

        # Afficher des informations de debug générales en haut
        debug_info = [
            f"DEBUG MODE ACTIVE (F3 to toggle)",
            f"Active paths: {len(pathfinder.debug_lines)}",
            f"Debug messages: {len([t for t in pathfinder.debug_texts if len(t) >= 4])}",
            f"Terrain map size: {len(pathfinder.terrain_map)} tiles",
            f"Lava zones: {len([t for t in pathfinder.terrain_map.values() if t == 'LAVA'])}",
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
                        print(
                            f"DEBUG LAVA avec caméra: ({x},{y}) -> base({pixel_x},{pixel_y}) -> caméra({camera_pos[0]},{camera_pos[1]})"
                        )
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
