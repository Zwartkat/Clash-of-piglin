# affichage, controle et IA, affichage c'est pour gérer la résolution de la page, contrôle pour rebind toutes les touches et IA,
# choisir quelle IA activée pour chaque troupe

import pygame

options_buttons = ["Resolution", "Fullscreen", "Volume", "IA Joueur", "Back"]

current_resolution = (800, 600)
fullscreen = False


def main():
    """
    Display the options menu and handle user interactions..
    Returns: (return_to_menu: bool, new_resolution: tuple, new_fullscreen: bool)
    """

    # get desktop / screen size reliably
    desktop_sizes = pygame.display.get_desktop_sizes()
    if desktop_sizes:
        desktop = tuple(desktop_sizes[0])
    else:
        info = pygame.display.Info()
        desktop = (info.current_w, info.current_h)

    # define candidate resolutions (ensure tuples only)
    candidate_resolutions = [
        (800, 600),
        (1024, 768),
        (1280, 720),
        (1920, 1080),
        desktop,
    ]

    # keep only resolutions that fit into the desktop and are valid tuples,
    # remove duplicates and sort (smallest -> largest)
    seen = set()
    possible_resolutions = []
    for r in candidate_resolutions:
        if not isinstance(r, tuple):
            continue
        if r[0] <= desktop[0] and r[1] <= desktop[1]:
            if r not in seen:
                seen.add(r)
                possible_resolutions.append(r)
    possible_resolutions.sort(key=lambda x: (x[0], x[1]))

    selected = 0
    running = True
    global current_resolution, fullscreen

    screen = pygame.display.set_mode(current_resolution)
    font = pygame.font.Font(None, 36)

    while running:
        # Draw options menu

        for i, button in enumerate(options_buttons):
            color = (255, 0, 0) if i == selected else (255, 255, 255)
            text = button
            if button == "Resolution":
                text += f": {current_resolution[0]}x{current_resolution[1]}"
            elif button == "Fullscreen":
                text += f": {'On' if fullscreen else 'Off'}"
            rendered_text = font.render(text, True, color)
            screen.blit(rendered_text, (50, 50 + i * 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, current_resolution, fullscreen
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options_buttons)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options_buttons)
                elif event.key == pygame.K_RETURN:
                    if options_buttons[selected] == "Resolution":
                        # Cycle through possible resolutions
                        current_index = possible_resolutions.index(current_resolution)
                        current_resolution = possible_resolutions[
                            (current_index + 1) % len(possible_resolutions)
                        ]
                        screen = pygame.display.set_mode(current_resolution)
                        pygame.display.flip()
                    elif options_buttons[selected] == "Fullscreen":
                        fullscreen = not fullscreen
                    elif options_buttons[selected] == "Back":
                        return True, current_resolution, fullscreen
