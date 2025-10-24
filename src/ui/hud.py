import esper
import pygame
from typing import Tuple
from core.services import Services
from core.player import Player
from components.health import Health
from events.victory_event import VictoryEvent
from enums.entity_type import EntityType
from config.units import UNITS
from components.cost import Cost
from components.position import Position
from systems.unit_factory import UnitFactory
from components.team import Team
from events.spawn_unit_event import SpawnUnitEvent

# from components.sprite import Sprite


class Hud:
    """Interface de jeu affichant les informations et permettant l'achat d'unités."""

    # non_spawnable_entities = ["BASTION", "BEACON"]

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
        self.background_color = (67, 37, 36)
        self.nether_brick_color = (44, 23, 26)
        self.netherrack_color = (97, 37, 36)
        self.gold_color = (255, 215, 0)
        self.text_color = (255, 255, 255)  # Blanc
        self.shadow_color = (0, 0, 0)
        self.team_colors = {
            1: (85, 255, 85),
            2: (255, 85, 85),
        }

        self.start_time = (
            Services.start_time if Services.start_time else pygame.time.get_ticks()
        )

        # huds dimensions
        self.hud_width = round(self.screen_width * 0.2)
        self.hud_height = round(self.screen_height * 0.98)

        # huds coordonates to ensure they are on the side of the screen
        self.team1_hud_x = round(self.screen_height * 0.01)
        self.team2_hud_x = (
            self.screen_width - self.hud_width - round(self.screen_height * 0.01)
        )
        self.hud_y = round(self.screen_height * 0.01)

        # Charger les textures
        self._load_textures()

        # Boutons d'achat d'unités pour chaque équipe
        self.team1_buttons = {}
        self.team2_buttons = {}
        self._init_unit_buttons()

        Services.event_bus.subscribe(VictoryEvent, self.on_victory)

        # Par défaut le Ghast est contrôlé par l'IA
        self.ghast_ai_controlled_by_player = True

    def _load_textures(self):
        """Charge les textures nécessaires pour le HUD"""
        self.textures = {}

        try:
            # Charger les sprites des unités pour les boutons
            self.textures["crossbowman"] = pygame.image.load(
                "assets/sprites/spritesheet-piglin.png"
            )
            self.textures["brute"] = pygame.image.load(
                "assets/sprites/spritesheet-brute.png"
            )
            self.textures["ghast"] = pygame.image.load(
                "assets/sprites/spritesheet-ghast.png"
            )

            # Redimensionner pour les boutons
            self.unit_icons = {}
            icon_size = 32

            # Extraire les icônes des spritesheets
            self.unit_icons[EntityType.CROSSBOWMAN] = pygame.Surface(
                (icon_size, icon_size), pygame.SRCALPHA
            )
            crossbow_sprite = pygame.transform.scale(
                self.textures["crossbowman"], (24 * 8, 24 * 8)
            )
            self.unit_icons[EntityType.CROSSBOWMAN].blit(
                crossbow_sprite, (0, 0), (0, 0, 24, 24)
            )
            self.unit_icons[EntityType.CROSSBOWMAN] = pygame.transform.scale(
                self.unit_icons[EntityType.CROSSBOWMAN], (icon_size, icon_size)
            )

            self.unit_icons[EntityType.BRUTE] = pygame.Surface(
                (icon_size, icon_size), pygame.SRCALPHA
            )
            brute_sprite = pygame.transform.scale(
                self.textures["brute"], (24 * 8, 24 * 8)
            )
            self.unit_icons[EntityType.BRUTE].blit(brute_sprite, (0, 0), (0, 0, 24, 24))
            self.unit_icons[EntityType.BRUTE] = pygame.transform.scale(
                self.unit_icons[EntityType.BRUTE], (icon_size, icon_size)
            )

            self.unit_icons[EntityType.GHAST] = pygame.Surface(
                (icon_size, icon_size), pygame.SRCALPHA
            )
            ghast_sprite = pygame.transform.scale(
                self.textures["ghast"], (24 * 8, 24 * 8)
            )
            self.unit_icons[EntityType.GHAST].blit(ghast_sprite, (0, 0), (0, 0, 24, 24))
            self.unit_icons[EntityType.GHAST] = pygame.transform.scale(
                self.unit_icons[EntityType.GHAST], (icon_size, icon_size)
            )

        except Exception as e:
            print(f"Erreur lors du chargement des textures: {e}")
            # Créer des icônes par défaut
            self.unit_icons = {}
            for unit_type in [
                EntityType.CROSSBOWMAN,
                EntityType.BRUTE,
                EntityType.GHAST,
            ]:
                icon = pygame.Surface((32, 32))
                icon.fill((100, 100, 100))
                self.unit_icons[unit_type] = icon

    def _init_unit_buttons(self):
        """Initialise les boutons d'achat d'unités pour chaque équipe avec design Minecraft"""
        button_width = self.hud_width - 30
        button_height = 50
        button_y_start = 200
        button_spacing = 60

        available_units = [EntityType.CROSSBOWMAN, EntityType.BRUTE, EntityType.GHAST]

        # Boutons pour l'équipe 1 (gauche)
        for i, unit_type in enumerate(available_units):
            y_pos = button_y_start + (i * button_spacing)
            button_rect = pygame.Rect(
                self.team1_hud_x + 15, y_pos, button_width, button_height
            )

            # Récupérer les informations de l'unité
            unit_entity = UNITS.get(unit_type)
            cost_component = unit_entity.get_component(Cost)

            self.team1_buttons[unit_type] = {
                "rect": button_rect,
                "cost": cost_component.amount,
                "name": unit_type.name,
                "hovered": False,
                "team": 1,
                "key": str(i + 1),  # Touches 1, 2, 3
            }

        # Boutons pour l'équipe 2 (droite)
        for i, unit_type in enumerate(available_units):
            y_pos = button_y_start + (i * button_spacing)
            button_rect = pygame.Rect(
                self.team2_hud_x + 15, y_pos, button_width, button_height
            )

            # Récupérer les informations de l'unité
            unit_entity = UNITS.get(unit_type)
            cost_component = unit_entity.get_component(Cost)

            self.team2_buttons[unit_type] = {
                "rect": button_rect,
                "cost": cost_component.amount,
                "name": unit_type.name,
                "hovered": False,
                "team": 2,
                "key": str(i + 7),  # Touches 7, 8, 9
            }

    def drawMinecraftPanel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        dark=False,
        dark_background=False,
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
        if dark_background:
            pygame.draw.rect(
                surface, tuple(max(0, c - 10) for c in base_color), inner_rect, 1
            )
        pygame.draw.rect(
            surface, tuple(max(0, c - 10) for c in base_color), inner_rect, 1
        )

    def drawMinecraftButton(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        hovered=False,
        pressed=False,
        enabled=True,
    ):
        """Dessine un bouton avec le style Minecraft"""
        # Couleur selon l'état
        if not enabled:
            base_color = (60, 60, 60)
        elif pressed:
            base_color = (80, 80, 80)
        elif hovered:
            base_color = (120, 120, 120)
        else:
            base_color = (100, 100, 100)

        # Fond du bouton
        surface.fill(base_color, rect)

        if not pressed:
            # Bordure claire (haut et gauche)
            light_color = tuple(min(255, c + 50) for c in base_color)
            pygame.draw.line(surface, light_color, rect.topleft, rect.topright, 2)
            pygame.draw.line(surface, light_color, rect.topleft, rect.bottomleft, 2)

            # Bordure sombre (bas et droite)
            dark_color = tuple(max(0, c - 50) for c in base_color)
            pygame.draw.line(surface, dark_color, rect.bottomleft, rect.bottomright, 2)
            pygame.draw.line(surface, dark_color, rect.topright, rect.bottomright, 2)
        else:
            # Effet enfoncé
            dark_color = tuple(max(0, c - 30) for c in base_color)
            pygame.draw.rect(surface, dark_color, rect, 2)

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

        hud_pos = 0 if team_id == 1 else self.screen_width - self.hud_width

        pygame.draw.rect(
            self.screen,
            self.background_color,
            (hud_pos, 0, self.hud_width, self.screen_height),
        )

        # adjust the position of the hud depending on the current team
        hud_x = self.team1_hud_x if team_id == 1 else self.team2_hud_x

        # create the panel for the team, with a background
        black_background = pygame.Rect(hud_x, 0, self.hud_width, self.screen_height)
        self.screen.fill(self.background_color, black_background)
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

        # Titre section unités
        units_y = info_y + 85
        units_title = self.font_medium.render("UNITES", True, self.text_color)
        # Ombre pour le titre
        units_shadow = self.font_medium.render("UNITES", True, self.shadow_color)
        self.screen.blit(units_shadow, (hud_x + 16, units_y + 1))
        self.screen.blit(units_title, (hud_x + 15, units_y))

        # Instructions pour les raccourcis (seulement équipe 1)
        if team_id == 1:
            # Affichage de l'état du Ghast
            ghast_status = "IA" if not self.ghast_ai_controlled_by_player else "JOUEUR"
            ghast_text = f"Ghast: {ghast_status}"
            ghast_surface = self.font_medium.render(ghast_text, True, self.text_color)
            self.screen.blit(ghast_surface, (hud_x + 60, info_y + 80))

            instructions = [
                "CONTROLES:",
                "K - Basculer IA/Joueur",
                "CTRL - Changer joueur",
                "1/2/3 - Acheter unite",
                "Clic - Selectionner",
                "Clic droit - Deplacer",
            ]

            y_start = self.hud_y + self.hud_height - 120
            for i, instruction in enumerate(instructions):
                color = self.gold_color if i == 0 else (200, 200, 200)
                font = self.font_small
                inst_surface = font.render(instruction, True, color)
                self.screen.blit(inst_surface, (hud_x + 10, y_start + (i * 18)))

    def draw_unit_buttons(self, team_id: int):
        """Dessine les boutons d'achat d'unités pour une équipe"""
        if (
            not Services.player_manager
            or team_id not in Services.player_manager.players
        ):
            return

        player = Services.player_manager.players[team_id]
        current_player_id = Services.player_manager.get_current_player()

        # Sélectionner les bons boutons selon l'équipe
        buttons = self.team1_buttons if team_id == 1 else self.team2_buttons

        for unit_type, button_info in buttons.items():
            rect = button_info["rect"]
            cost = button_info["cost"]
            hovered = button_info["hovered"]
            key = button_info["key"]

            # Vérifier si le joueur peut acheter (seulement si c'est son tour)
            can_afford = player.money >= cost
            is_current_turn = team_id == current_player_id
            enabled = is_current_turn and can_afford

            # Dessiner le bouton avec style Minecraft
            self.drawMinecraftButton(
                self.screen, rect, hovered=hovered, enabled=enabled
            )

            # Icône de l'unité
            if unit_type in self.unit_icons:
                icon_x = rect.x + 8
                icon_y = rect.y + 9
                self.screen.blit(self.unit_icons[unit_type], (icon_x, icon_y))

            # Nom de l'unité
            unit_name = self._get_unit_display_name(unit_type)
            name_color = self.text_color if enabled else (120, 120, 120)
            name_surface = self.font_small.render(unit_name, True, name_color)
            name_x = rect.x + 50
            name_y = rect.y + 8
            self.screen.blit(name_surface, (name_x, name_y))

            # Coût en or
            cost_text = f"{cost} Or"
            cost_color = self.gold_color if enabled else (150, 120, 0)
            cost_surface = self.font_small.render(cost_text, True, cost_color)
            cost_x = rect.x + 50
            cost_y = rect.y + 25
            self.screen.blit(cost_surface, (cost_x, cost_y))

            # Raccourci clavier
            if is_current_turn:
                key_text = f"[{key}]"
                key_surface = self.font_small.render(key_text, True, (200, 200, 200))
                key_rect = key_surface.get_rect()
                key_x = rect.right - key_rect.width - 8
                key_y = rect.y + 5
                self.screen.blit(key_surface, (key_x, key_y))

    def buy_unit_by_key(self, unit_type: EntityType, team_id: int) -> bool:
        """Achète une unité via raccourci clavier"""
        if not Services.player_manager:
            return False

        # Utiliser l'équipe spécifiée au lieu de l'équipe actuelle
        player = Services.player_manager.players.get(team_id)

        if not player:
            return False

        return self._try_buy_unit(unit_type, player, team_id)

    def _get_unit_display_name(self, unit_type: EntityType) -> str:
        """Retourne le nom d'affichage d'une unité"""
        names = {
            EntityType.CROSSBOWMAN: "Arbaletrier",
            EntityType.BRUTE: "Brute",
            EntityType.GHAST: "Ghast",
        }
        return names.get(unit_type, unit_type.name)

    def handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Gère le survol des boutons"""
        # Équipe 1
        for unit_type, button_info in self.team1_buttons.items():
            button_info["hovered"] = button_info["rect"].collidepoint(mouse_pos)

        # Équipe 2
        for unit_type, button_info in self.team2_buttons.items():
            button_info["hovered"] = button_info["rect"].collidepoint(mouse_pos)

    def handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Gère les clics sur les boutons d'achat"""
        if not Services.player_manager:
            return False

        current_player_id = Services.player_manager.get_current_player()
        current_player = Services.player_manager.players.get(current_player_id)

        if not current_player:
            return False

        # Vérifier les boutons de l'équipe 1
        for unit_type, button_info in self.team1_buttons.items():
            if (
                button_info["rect"].collidepoint(mouse_pos)
                and button_info["team"] == current_player_id
            ):
                return self._try_buy_unit(unit_type, current_player, current_player_id)

        # Vérifier les boutons de l'équipe 2
        for unit_type, button_info in self.team2_buttons.items():
            if (
                button_info["rect"].collidepoint(mouse_pos)
                and button_info["team"] == current_player_id
            ):
                return self._try_buy_unit(unit_type, current_player, current_player_id)

        return False

    def _try_buy_unit(
        self, unit_type: EntityType, player: Player, team_id: int
    ) -> bool:
        """Tente d'acheter une unité"""
        # Récupérer le coût
        unit_entity = UNITS.get(unit_type)
        cost_component = unit_entity.get_component(Cost)
        cost = cost_component.amount

        if player.money >= cost:
            # Créer l'unité près du bastion du joueur
            spawn_pos = self._get_spawn_position(player)
            team = Team(team_id)

            # Créer l'unité via l'événement
            Services.event_bus.emit(SpawnUnitEvent(unit_type, team, spawn_pos))

            # Déduire le coût
            player.money -= cost
            return True
            # except Exception as e:
            #     print(f"Erreur lors de la création de l'unité: {e}")
        return False

    def _get_spawn_position(self, player: Player) -> Position:
        """Détermine la position de spawn devant le bastion du joueur"""
        try:
            # Récupérer la position du bastion
            if esper.has_component(player.bastion, Position):
                bastion_pos = esper.component_for_entity(player.bastion, Position)

                # Spawn du bastion selon l'équipe
                if player.team_number == 1:
                    return Position(bastion_pos.x + 150, bastion_pos.y + 50)
                else:
                    return Position(bastion_pos.x - 150, bastion_pos.y - 50)
        except:
            pass

        # default position if the bastion is not found
        if player.team_number == 1:
            return Position(150, 150)
        else:
            return Position(650, 650)

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

        # text shadow
        shadow_surface = self.font_large.render(victory_message, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(
            center=(
                self.screen.get_width() // 2 + 3,
                self.screen.get_height() // 2 - 47,
            )
        )

        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(victory_surface, victory_rect)

        # secondary message
        sub_message = "Appuyez sur ECHAP pour quitter"
        sub_surface = self.font_medium.render(sub_message, True, (255, 255, 255))
        sub_rect = sub_surface.get_rect(
            center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 20)
        )
        self.screen.blit(sub_surface, sub_rect)

        # time spent since victory
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

    def is_click_on_hud(self, mouse_pos: Tuple[int, int]) -> bool:
        """Vérifie si le clic est sur l'un des HUD"""
        # Zone HUD équipe 1
        team1_area = pygame.Rect(
            self.team1_hud_x, self.hud_y, self.hud_width, self.hud_height
        )
        # Zone HUD équipe 2
        team2_area = pygame.Rect(
            self.team2_hud_x, self.hud_y, self.hud_width, self.hud_height
        )

        return team1_area.collidepoint(mouse_pos) or team2_area.collidepoint(mouse_pos)

    def draw(self):
        """Dessine l'interface complète"""
        self.drawTimeDisplay()
        self.drawTeamHud(1)
        self.drawTeamHud(2)
        self.draw_unit_buttons(1)
        self.draw_unit_buttons(2)
        if self.victory_team:
            self.draw_victory_screen()
