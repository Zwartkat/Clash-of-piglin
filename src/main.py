from typing import Tuple
import esper
import pygame
import os

os.environ["SDL_VIDEO_CENTERED"] = "1"
from core.data_bus import DATA_BUS
from core.debugger import Debugger
from core.ecs.event_bus import EventBus
from core.config import Config
from enums.data_bus_key import DataBusKey
from systems.sound_system import SoundSystem
import core.engine as game_manager
import core.options as option
from ui.options_menu import OptionsMenu

DATA_BUS.replace(DataBusKey.DEBUGGER, Debugger(enable_warn=True, enable_error=True))
DATA_BUS.get_debugger().log("Démarrage du jeu")

Config.load("config.yaml")

DATA_BUS.register(DataBusKey.CONFIG, Config)
DATA_BUS.register(DataBusKey.EVENT_BUS, EventBus.get_event_bus())


pygame.init()
pygame.display.set_caption(Config.get(key="game_name"))

screen = pygame.display.set_mode(option.current_resolution, option.flags)

font = pygame.font.Font(Config.get_assets(key="font"), 18)

background = pygame.image.load(Config.get_assets(key="background")).convert()
background = pygame.transform.scale(background, option.current_resolution)

logo = pygame.image.load(Config.get_assets(key="logo")).convert_alpha()
logo = pygame.transform.scale(logo, (180, 270))

pygame.display.set_icon(logo)

menu_items = Config.get(key="menu_buttons")
selected = 0

SoundSystem.set_music(SoundSystem.MUSICS["pigstep"])
SoundSystem.set_music_volume(0.1)
SoundSystem.play_music()

play_options_open = False
play_modes = ["Joueur vs IA", "IA vs IA"]
play_option_rects = [
    pygame.Rect(250, 250 + i * 100, 300, 60) for i in range(len(play_modes))
]

credits_open = False
credits_text = [
    "Crédits",
    "",
    "Développeurs:",
    "- Zwartkat",
    "- xMegumi",
    "- darkell",
    "- WorKai",
    "- Sparkness",
    "- MatthieuPinceel",
    "Graphismes: Zwartkat,Mojang Studio",
    "",
    "Jeu inspiré de la license Minecraft dont les droits",
    "reviennent à Mojang Studios (Microsoft)",
]
scroll_offset = 0
scroll_speed = 0


def draw_credits():
    global scroll_offset

    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    screen_width = screen.get_width()
    start_y = 50 - scroll_offset
    for line in credits_text:
        text_surf = font.render(line, True, (255, 255, 255))
        screen.blit(
            text_surf, (screen_width // 2 - text_surf.get_width() // 2, start_y)
        )
        start_y += 40

    scroll_offset += scroll_speed
    if start_y < 0:
        scroll_offset = 0


# Draw a button
def draw_button(surface, rect, text, hovered):
    """
    Display a button in the main menu with hover effect.

    Args:
        surface (pygame.Surface): Surface on which to draw the button.
        rect (pygame.Rect): Rectangle defining the button's position and size.
        text (str): Text to display on the button.
        hovered (bool): Indicates if the button is hovered.
    """

    base_color: Tuple[int] = (198, 198, 198) if not hovered else (165, 165, 165)

    shadow_color = (60, 60, 60)
    border_color = (80, 80, 80)

    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=8)
    pygame.draw.rect(surface, base_color, rect, border_radius=8)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)

    text_surf = font.render(text, True, (40, 40, 40))
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)


button_rects = [pygame.Rect(225, 220 + i * 50, 350, 40) for i in range(len(menu_items))]


def draw_menu():
    """
    Display the main menu.
    """
    # Ensure assets and button rects are up-to-date with the current screen size
    apply_display_settings()

    screen.blit(background, (0, 0))

    # center logo horizontally and keep same vertical offset
    logo_x = (screen.get_width() - logo.get_width()) // 2
    screen.blit(logo, (logo_x, -20))

    for i, rect in enumerate(button_rects):
        hovered: bool = rect.collidepoint(pygame.mouse.get_pos())
        draw_button(screen, rect, menu_items[i], hovered)

    if play_options_open:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        screen_width = screen.get_width()
        title_surf = font.render("Choisir le mode de jeu", True, (255, 255, 255))
        screen.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2, 150))

        for i, rect in enumerate(play_option_rects):
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            draw_button(screen, rect, play_modes[i], hovered)

    info_font = pygame.font.Font(Config.get_assets(key="font"), 12)
    info_text = info_font.render("Presque pas Minecraft 1.16", True, (220, 220, 220))
    screen.blit(info_text, (20, screen.get_height() - 20))


credits_open = False  # global
option_open = False  # global


def apply_display_settings():
    """
    Rescale background, logo and recreate button_rects proportionally to current screen size.
    Does not decide the display mode (set_mode should be called by caller if needed).
    """
    global screen, background, logo, button_rects, play_option_rects

    w, h = screen.get_size()
    base_w, base_h = 800, 600

    # Background scaled to fill screen
    background_img = pygame.image.load(Config.get_assets(key="background")).convert()
    background = pygame.transform.scale(background_img, (w, h))

    # Logo: scale relative to base sizes (1024x1536)
    logo_img = pygame.image.load(Config.get_assets(key="logo")).convert_alpha()
    logo_w = max(1, int(180 * w / base_w))
    logo_h = max(1, int(270 * h / base_h))
    logo = pygame.transform.scale(logo_img, (logo_w, logo_h))
    pygame.display.set_icon(logo)

    # Buttons: positions/sizes proportional to base layout
    btn_w = max(1, int(350 * w / base_w))
    btn_h = max(1, int(40 * h / base_h))
    start_x = int(225 * w / base_w)
    start_y = int(220 * h / base_h)
    gap = int(50 * h / base_h)
    button_rects = [
        pygame.Rect(start_x, start_y + i * gap, btn_w, btn_h)
        for i in range(len(menu_items))
    ]

    # Play options buttons: centered horizontally
    play_btn_w = max(1, int(300 * w / base_w))
    play_btn_h = max(1, int(60 * h / base_h))
    play_start_x = (w - play_btn_w) // 2  # Centered
    play_start_y = int(250 * h / base_h)
    play_gap = int(100 * h / base_h)
    play_option_rects = [
        pygame.Rect(play_start_x, play_start_y + i * play_gap, play_btn_w, play_btn_h)
        for i in range(len(play_modes))
    ]


# Initial apply to setup assets/button rects for the current screen
apply_display_settings()


def handle_click(pos: Tuple[int]):
    """
    Handle click on the main menu.
    """
    # ajouter play_options_open ici pour éviter UnboundLocalError
    global selected, credits_open, screen, play_options_open

    if credits_open:
        credits_open = False
        return True
    #
    # if option_open:
    #    option_open = False
    #    return True

    # Si le sous-menu Play est ouvert, gérer ses clics
    if play_options_open:
        # clic sur une option de jeu
        for i, rect in enumerate(play_option_rects):
            if rect.collidepoint(pos):
                SoundSystem.play_button_clicked()
                chosen = play_modes[i]
                if chosen == play_modes[0]:  # Joueur vs IA
                    return_to_menu = game_manager.main(screen, ia_mode="jcia")
                else:  # IA vs IA
                    return_to_menu = game_manager.main(screen, ia_mode="iacia")

                play_options_open = False
                if return_to_menu:
                    # Get current screen instead of creating new one
                    screen = pygame.display.get_surface()
                    if screen is None:
                        screen = pygame.display.set_mode(
                            option.current_resolution, option.flags
                        )
                    apply_display_settings()
                    return True
                return False
        # clic hors des options ferme le sous-menu
        play_options_open = False
        return True

    for i, rect in enumerate(button_rects):
        if rect.collidepoint(pos):
            SoundSystem.play_button_clicked()
            selected = i
            if menu_items[selected] == menu_items[0]:  # Play
                # ouvrir le sous-menu Play au lieu de lancer directement
                play_options_open = True
                return True
            elif menu_items[selected] == menu_items[1]:  # Options ou Crédits
                print("Credits opened")
                credits_open = True
            elif menu_items[selected] == menu_items[2]:  # Options
                print("Options")
                option_open = True
                options_menu = OptionsMenu(option.current_resolution, option.flags)
                return_to_menu, new_res, new_flags = options_menu.run(screen)
                if return_to_menu:
                    option.current_resolution = new_res
                    option.flags = new_flags
                    # Only recreate display if settings changed
                    if new_res != screen.get_size() or new_flags != (
                        screen.get_flags() & pygame.FULLSCREEN
                    ):
                        try:
                            screen = pygame.display.set_mode(new_res, new_flags)
                        except Exception as e:
                            print(f"Failed to apply display settings: {e}")
                            # Fallback to current settings
                            screen = pygame.display.get_surface()
                    else:
                        screen = pygame.display.get_surface()
                    apply_display_settings()
                    return True
            elif menu_items[selected] == menu_items[3]:  # Quit
                print("Quit")
                pygame.quit()
                exit()
            break
    return True


running = True
while running:
    draw_menu()
    if credits_open:
        draw_credits()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            print(running)
            running = handle_click(event.pos)

    pygame.display.flip()
pygame.quit()
