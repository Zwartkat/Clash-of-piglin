import pygame
from ui.hud import Hud
from enums.entity_type import EntityType


class HudSystem:
    """Système gérant l'interface utilisateur du jeu"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.hud = Hud(screen)

    def draw(self):
        """Dessine l'interface"""
        self.hud.draw()

    def process_event(self, event):
        """Traite les événements liés à l'interface"""
        # if event.type == pygame.MOUSEMOTION:
        #     self.hud.handle_mouse_motion(event.pos)
        #     return False  # Laisser passer les mouvements de souris
        # elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        #     # Vérifier si le clic est sur l'interface
        #     if self.hud.is_click_on_hud(event.pos):
        #         return self.hud.handle_mouse_click(event.pos)
        #     return False  # Laisser passer les clics sur la map
        # elif event.type == pygame.KEYDOWN:
        #     # Gestion des raccourcis clavier pour l'achat d'unités
        #     # Équipe 1 (touches 1, 2, 3)
        #     if event.key == pygame.K_1:
        #         return self.hud.buy_unit_by_key(EntityType.CROSSBOWMAN, 1)
        #     elif event.key == pygame.K_2:
        #         return self.hud.buy_unit_by_key(EntityType.BRUTE, 1)
        #     elif event.key == pygame.K_3:
        #         return self.hud.buy_unit_by_key(EntityType.GHAST, 1)
        #     # Équipe 2 (touches 7, 8, 9)
        #     elif event.key == pygame.K_7:
        #         return self.hud.buy_unit_by_key(EntityType.CROSSBOWMAN, 2)
        #     elif event.key == pygame.K_8:
        #         return self.hud.buy_unit_by_key(EntityType.BRUTE, 2)
        #     elif event.key == pygame.K_9:
        #         return self.hud.buy_unit_by_key(EntityType.GHAST, 2)
        #     return False
        if event.type == pygame.VIDEORESIZE:
            # Recréer le HUD avec les nouvelles dimensions
            self.hud = Hud(self.screen)
            return False
        return False
