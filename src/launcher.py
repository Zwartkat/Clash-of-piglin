from typing import Tuple
import pygame
import core.game_launcher as game_manager

from core.config import Config

Config.load()

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

# pygame.mixer.music.load("assets/audio/pigstep.mp3")
# pygame.mixer.music.set_volume(1)
# pygame.mixer.music.play(-1)


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

    info_font = pygame.font.Font(Config.get_assets(key="font"), 12)
    info_text = info_font.render("Presque Minecraft 1.16", True, (220, 220, 220))
    screen.blit(info_text, (20, 580))

    pygame.display.flip()


def handle_click(pos: Tuple[int]):
    """
    Handle click on the main menu.

    Args:
        pos (tuple): Mouse click position.

    Returns:
        bool: False if the game should quit, True otherwise.
    """
    global selected
    for i, rect in enumerate(button_rects):
        if rect.collidepoint(pos):
            selected = i
            if menu_items[selected] == menu_items[0]:  # Play
                return game_manager.main(screen)
            elif menu_items[selected] == menu_items[1]:  # Options
                pass
            elif menu_items[selected] == menu_items[2]:  # Quit
                return False
        return True


running = True
while running:
    draw_menu()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            running = handle_click(event.pos)
pygame.quit()
