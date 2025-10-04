import pygame
from core.services import Services


class Hud:
    """Interface de jeu affichant les informations et permettant l'achat d'unités."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        try:
            self.font_large = pygame.font.Font(
                "assets/fonts/Minecraftia-Regular.ttf", 20
            )
            self.font_medium = pygame.font.Font(
                "assets/fonts/Minecraftia-Regular.ttf", 16
            )
            self.font_small = pygame.font.Font(
                "assets/fonts/Minecraftia-Regular.ttf", 12
            )
        except:
            self.font_large = pygame.font.Font(None, 28)
            self.font_medium = pygame.font.Font(None, 22)
            self.font_small = pygame.font.Font(None, 16)

        # colors used in the huds
        self.nether_brick_color = (44, 23, 26)
        self.netherrack_color = (97, 37, 36)
        self.gold_color = (255, 215, 0)
        self.shadow_color = (0, 0, 0)
        self.team_colors = {
            1: (85, 255, 85),
            2: (255, 85, 85),
        }

        # TODO :
        # Faire en sorte que la fenêtre devienne responsive et modifier le commentaire/code

        # huds dimensions (should be responsive - aren't)
        self.hud_width = round(self.screen_width * 0.2)
        self.hud_height = round(self.screen_height * 0.9)

        # huds coordonates to ensure they are on the side of the screen
        self.team1_hud_x = round(self.screen_height * 0.01)
        self.team2_hud_x = (
            self.screen_width - self.hud_width - round(self.screen_height * 0.01)
        )
        self.hud_y = round(self.screen_height * 0.01)

    def drawMinecraftPanel(
        self, surface: pygame.Surface, rect: pygame.Rect, dark=False
    ):
        """Dessine un panneau avec le style Minecraft"""

        # base color for the panel
        base_color = self.nether_brick_color if dark else self.netherrack_color
        surface.fill(base_color, rect)

        # adding a 3D-simulating border to the panel
        light_color = tuple(min(255, c + 30) for c in base_color)
        pygame.draw.line(surface, light_color, rect.topleft, rect.topright, 2)
        pygame.draw.line(surface, light_color, rect.topleft, rect.bottomleft, 2)
        dark_color = tuple(max(0, c - 30) for c in base_color)
        pygame.draw.line(surface, dark_color, rect.bottomleft, rect.bottomright, 2)
        pygame.draw.line(surface, dark_color, rect.topright, rect.bottomright, 2)

        inner_rect = pygame.Rect(
            rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4
        )
        pygame.draw.rect(
            surface, tuple(max(0, c - 10) for c in base_color), inner_rect, 1
        )

    def drawTeamHud(self, team_id: int):
        """Dessine le HUD d'une équipe spécifique"""
        if (
            not Services.player_manager
            or team_id not in Services.player_manager.players
        ):
            return

        current_player = Services.player_manager.get_current_player()

        # adjust the position of the hud depending on the current team
        hud_x = self.team1_hud_x if team_id == 1 else self.team2_hud_x

        # create the panel for the team
        main_panel = pygame.Rect(hud_x, self.hud_y, self.hud_width, self.hud_height)
        self.drawMinecraftPanel(
            self.screen, main_panel, dark=(team_id == current_player)
        )

        # text for the title
        title_text = f"EQUIPE {team_id}"
        # adding the shadow
        shadow_surface = self.font_large.render(title_text, True, self.shadow_color)
        shadow_rect = shadow_surface.get_rect(
            centerx=hud_x + self.hud_width // 2 + 2, y=self.hud_y + 12
        )
        self.screen.blit(shadow_surface, shadow_rect)
        # adding the title
        title_surface = self.font_large.render(
            title_text, True, self.team_colors[team_id]
        )
        title_rect = title_surface.get_rect(
            centerx=hud_x + self.hud_width // 2, y=self.hud_y + 10
        )
        self.screen.blit(title_surface, title_rect)

        # adding the current team indicator
        if team_id == current_player:
            active_text = ">>> TOUR ACTUEL <<<"
            active_surface = self.font_small.render(active_text, True, self.gold_color)
            active_rect = active_surface.get_rect(
                centerx=hud_x + self.hud_width // 2, y=self.hud_y + 40
            )
            self.screen.blit(active_surface, active_rect)

    def draw(self):
        """Dessine l'interface complète"""
        self.drawTeamHud(1)
        self.drawTeamHud(2)
