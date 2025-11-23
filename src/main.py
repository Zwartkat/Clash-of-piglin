from typing import Tuple
import esper
import pygame
from core.data_bus import DATA_BUS
from core.debugger import Debugger
from core.ecs.event_bus import EventBus
from core.config import Config
from enums.data_bus_key import DataBusKey
from systems.sound_system import SoundSystem

DATA_BUS.replace(DataBusKey.DEBUGGER, Debugger(enable_warn=True, enable_error=True))
DATA_BUS.get_debugger().log("Démarrage du jeu")

Config.load("config.yaml")

DATA_BUS.register(DataBusKey.CONFIG, Config)
DATA_BUS.register(DataBusKey.EVENT_BUS, EventBus.get_event_bus())

import core.engine as game_manager


pygame.init()
pygame.display.set_caption(Config.get(key="game_name"))

screen = pygame.display.set_mode((800, 600))

font = pygame.font.Font(Config.get_assets(key="font"), 18)

background = pygame.image.load(Config.get_assets(key="background")).convert()
background = pygame.transform.scale(background, (800, 600))

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
    pygame.Rect(300, 250 + i * 50, 200, 30) for i in range(len(play_modes))
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

    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    start_y = 50 - scroll_offset
    for line in credits_text:
        text_surf = font.render(line, True, (255, 255, 255))
        screen.blit(text_surf, (400 - text_surf.get_width() // 2, start_y))
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
    screen.blit(background, (0, 0))
    screen.blit(logo, (310, -20))

    for i, rect in enumerate(button_rects):
        hovered: bool = rect.collidepoint(pygame.mouse.get_pos())
        draw_button(screen, rect, menu_items[i], hovered)

    if play_options_open:
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title_surf = font.render("Choisir le mode de jeu", True, (255, 255, 255))
        screen.blit(title_surf, (400 - title_surf.get_width() // 2, 150))

        for i, rect in enumerate(play_option_rects):
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            draw_button(screen, rect, play_modes[i], hovered)

    info_font = pygame.font.Font(Config.get_assets(key="font"), 12)
    info_text = info_font.render("Presque pas Minecraft 1.16", True, (220, 220, 220))
    screen.blit(info_text, (20, 580))


credits_open = False  # global


def handle_click(pos: Tuple[int]):
    """
    Handle click on the main menu.
    """
    # ajouter play_options_open ici pour éviter UnboundLocalError
    global selected, credits_open, screen, play_options_open

    if credits_open:
        credits_open = False
        return True

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
                    screen = pygame.display.set_mode((800, 600))
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
            elif menu_items[selected] == menu_items[2]:  # Quit
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
