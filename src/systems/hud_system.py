import pygame
from ui.hud import Hud


class HudSystem:
    """Système gérant l'interface utilisateur du jeu"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.hud = Hud(screen)

    def draw(self):
        """Dessine l'interface"""
        self.hud.draw()
