import pygame
import core.game_launcher as game_manager

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Clash of Piglin - Main Menu")

font = pygame.font.Font("assets/fonts/Minecraftia-Regular.ttf", 18)

background = pygame.image.load("assets/background2.jpg").convert()
background = pygame.transform.scale(background, (800, 600))

logo = pygame.image.load("assets/images/logo.png").convert_alpha()
logo = pygame.transform.scale(logo, (180, 270))

pygame.display.set_icon(logo)

menu_items = ["Play", "Credits", "Quit"]
selected = 0

# pygame.mixer.music.load("assets/audio/pigstep.mp3")
# pygame.mixer.music.set_volume(1)
# pygame.mixer.music.play(-1)


def draw_mc_button(surface, rect, text, hovered):

    if hovered:
        base_color = (165, 165, 165)
    else:
        base_color = (198, 198, 198)

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
    screen.blit(background, (0, 0))
    screen.blit(logo, (310, -20))
    for i, rect in enumerate(button_rects):
        hovered: bool = rect.collidepoint(pygame.mouse.get_pos())
        draw_mc_button(screen, rect, menu_items[i], hovered)
    info_font = pygame.font.Font("assets/fonts/Minecraftia-Regular.ttf", 12)
    info_text = info_font.render("Presque Minecraft 1.16", True, (220, 220, 220))
    screen.blit(info_text, (20, 580))
    pygame.display.flip()


def handle_click(pos):
    global selected
    for i, rect in enumerate(button_rects):
        if rect.collidepoint(pos):
            selected = i
            if menu_items[selected] == "Play":
                return game_manager.main(screen)
            elif menu_items[selected] == "Credits":
                print("Credits!")
            elif menu_items[selected] == "Quit":
                pygame.quit()
                exit()


running = True
while running:
    draw_menu()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            running = handle_click(event.pos)

pygame.quit()
