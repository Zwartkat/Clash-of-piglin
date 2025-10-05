import esper
import pygame
from core.services import Services
from core.player import Player
from components.health import Health
from events.victory_event import VictoryEvent


class Hud:
    """Interface de jeu affichant les informations et permettant l'achat d'unités."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        self.victory_team: int = None
        self.lose_team: int = None

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

        self.start_time = (
            Services.start_time if Services.start_time else pygame.time.get_ticks()
        )

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

        Services.event_bus.subscribe(VictoryEvent, self.on_victory)

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

    def getGameTime(self) -> str:
        """Retourne le temps de jeu formaté."""
        if self.victory_team:
            elapsed_ms = Services.finish_time - Services.start_time
        else:
            elapsed_ms = pygame.time.get_ticks() - Services.start_time
        elapsed_seconds = elapsed_ms // 1000
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def drawTimeDisplay(self):
        """Affiche le temps de jeu au centre en haut de l'écran."""
        time_text = f"Temps: {self.getGameTime()}"
        time_surface = self.font_large.render(time_text, True, self.gold_color)

        # panel for the clock
        panel_width = time_surface.get_width() + 30
        panel_height = time_surface.get_height() + 20
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = 10

        time_panel = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self.drawMinecraftPanel(self.screen, time_panel)

        # Ombre du texte
        shadow_surface = self.font_large.render(time_text, True, self.shadow_color)
        shadow_rect = shadow_surface.get_rect(
            centerx=self.screen_width // 2 + 2, y=panel_y + 12
        )
        self.screen.blit(shadow_surface, shadow_rect)

        # diaplaying the title
        time_rect = time_surface.get_rect(
            centerx=self.screen_width // 2, y=panel_y + 10
        )
        self.screen.blit(time_surface, time_rect)

    def get_bastion_health(self, player: Player) -> int:
        """Récupère la vie du bastion d'un joueur"""
        try:
            if esper.has_component(player.bastion, Health):
                health_component = esper.component_for_entity(player.bastion, Health)
                return health_component.remaining
        except:
            pass
        return 0

    def drawTeamHud(self, team_id: int):
        """Dessine le HUD d'une équipe spécifique"""
        if (
            not Services.player_manager
            or team_id not in Services.player_manager.players
        ):
            return

        player = Services.player_manager.players[team_id]
        current_player = Services.player_manager.get_current_player()
        print("Team", team_id, current_player)

        # adjust the position of the hud depending on the current team
        hud_x = self.team1_hud_x if team_id == 1 else self.team2_hud_x

        # create the panel for the team
        main_panel = pygame.Rect(hud_x, self.hud_y, self.hud_width, self.hud_height)
        self.drawMinecraftPanel(
            self.screen, main_panel, dark=(team_id != current_player)
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
        print("Current", team_id == current_player, current_player)
        if team_id == current_player:
            active_text = ">>> TOUR ACTUEL <<<"
            active_surface = self.font_small.render(active_text, True, self.gold_color)
            active_rect = active_surface.get_rect(
                centerx=hud_x + self.hud_width // 2, y=self.hud_y + 40
            )
            self.screen.blit(active_surface, active_rect)

        # parameter used to place the player's info
        info_y = self.hud_y + 70

        # creating the text to show the amount of gold the player has
        money_text = f"Or: {int(player.money)}/1500"
        money_surface = self.font_medium.render(money_text, True, self.gold_color)
        self.screen.blit(money_surface, (hud_x + 15, info_y))

        # displaying a progress bar to show the amount of gold the player has
        money_progress = min(player.money / 1500.0, 1.0)
        bar_width = self.hud_width - 30
        bar_height = 12
        bar_x = hud_x + 15
        bar_y = info_y + 20

        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        self.drawMinecraftPanel(self.screen, bar_rect, dark=True)

        # filling the bar
        if money_progress > 0:
            progress_width = int((bar_width - 4) * money_progress)
            progress_rect = pygame.Rect(
                bar_x + 2, bar_y + 2, progress_width, bar_height - 4
            )
            self.screen.fill(self.gold_color, progress_rect)

        # displaying in text the health of the player's bastion
        bastion_health = self.get_bastion_health(player)
        health_text = f"Bastion: {bastion_health}/1000"
        health_color = (255, 100, 100) if bastion_health < 300 else (100, 255, 100)
        health_surface = self.font_medium.render(health_text, True, health_color)
        self.screen.blit(health_surface, (hud_x + 15, info_y + 40))

        # displaying a progress bar to show the health of the player's bastion
        health_progress = bastion_health / 1000.0
        health_bar_y = info_y + 60

        health_bar_rect = pygame.Rect(bar_x, health_bar_y, bar_width, bar_height)
        self.drawMinecraftPanel(self.screen, health_bar_rect, dark=True)

        # filling the bar
        if health_progress > 0:
            health_width = int((bar_width - 4) * health_progress)
            health_fill_rect = pygame.Rect(
                bar_x + 2, health_bar_y + 2, health_width, bar_height - 4
            )
            health_bar_color = (
                (255, 100, 100)
                if health_progress < 0.3
                else (255, 200, 100) if health_progress < 0.6 else (100, 255, 100)
            )
            self.screen.fill(health_bar_color, health_fill_rect)

    def draw_victory_screen(self):
        """
        Draw victory screen

        Args:
            victory_event (VictoryEvent): An emit VictoryEvent
        """
        victory_message = f"VICTOIRE DE L'EQUIPE {self.victory_team}!"

        overlay = pygame.Surface(
            (self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        victory_surface = self.font_large.render(victory_message, True, (255, 215, 0))
        victory_rect = victory_surface.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 50)
        )

        # Ombre du texte
        shadow_surface = self.font_large.render(victory_message, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(
            center=(
                self.screen.get_width() // 2 + 3,
                self.screen.get_height() // 2 - 47,
            )
        )

        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(victory_surface, victory_rect)

        # Message secondaire
        sub_message = "Appuyez sur ECHAP pour quitter"
        sub_surface = self.font_medium.render(sub_message, True, (255, 255, 255))
        sub_rect = sub_surface.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 20)
        )
        self.screen.blit(sub_surface, sub_rect)

        # Temps écoulé depuis la victoire
        elapsed_time = (Services.finish_time - Services.start_time) // 1000
        time_message = (
            f"Partie terminee en {elapsed_time // 60}:{elapsed_time % 60:02d}"
        )
        time_surface = self.font_medium.render(time_message, True, (200, 200, 200))
        time_rect = time_surface.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 60)
        )
        self.screen.blit(time_surface, time_rect)

    def on_victory(self, victory_event: VictoryEvent):
        self.victory_team = victory_event.winning_team
        self.lose_team = victory_event.losing_team

    def draw(self):
        """Dessine l'interface complète"""
        self.drawTimeDisplay()
        self.drawTeamHud(1)
        self.drawTeamHud(2)
        if self.victory_team:
            self.draw_victory_screen()
