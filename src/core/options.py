# affichage, controle et IA, affichage c'est pour gérer la résolution de la page, contrôle pour rebind toutes les touches et IA,
# choisir quelle IA activée pour chaque troupe

import pygame

options_buttons = ["Resolution", "Fullscreen", "Volume", "IA Joueur", "Back"]

current_resolution = (1280, 720)
flags = 0
fullscreen = False
# volume 0.0 - 1.0
current_volume = 0.8


def main():

    selected = 0
    running = True
    dragging = False
    global current_resolution, flags, fullscreen, current_volume

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

    screen = pygame.display.set_mode(current_resolution, flags)
    font = pygame.font.Font(None, 36)

    # try to init mixer and optionally play a short preview (non-blocking)
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception:
        pass

    # set mixer volume if possible
    try:
        pygame.mixer.music.set_volume(current_volume)
    except Exception:
        pass

    while running:
        sw, sh = screen.get_size()

        # slider geometry (draw under the menu when "Volume" is selected)
        slider_w = max(220, int(sw * 0.4))
        slider_h = 10
        slider_x = (sw - slider_w) // 2
        # place slider a bit below the list of options (match menu y positions)
        slider_y = int(50 + 2 * 50 + 24)  # under the 3rd item roughly

        handle_w = 14
        handle_h = 26

        # compute handle position from current_volume (0.0 -> left, 1.0 -> right)
        handle_x = int(slider_x + current_volume * (slider_w - handle_w))
        handle_y = slider_y + slider_h // 2 - handle_h // 2
        handle_rect = pygame.Rect(handle_x, handle_y, handle_w, handle_h)
        slider_rect = pygame.Rect(slider_x, slider_y, slider_w, slider_h)

        # Draw options menu text
        screen.fill((30, 30, 30))

        for i, button in enumerate(options_buttons):
            color = (255, 0, 0) if i == selected else (255, 255, 255)
            text = button
            if button == "Resolution":
                text += f": {current_resolution[0]}x{current_resolution[1]}"
            elif button == "Fullscreen":
                text += f": {'On' if fullscreen else 'Off'}"
            elif button == "Volume":
                text += f": {int(current_volume * 100)}%"

            rendered_text = font.render(text, True, color)
            screen.blit(rendered_text, (50, 50 + i * 50))

        # If Volume line is visible, draw slider UI
        vol_index = options_buttons.index("Volume")
        vol_y = 50 + vol_index * 50
        # draw slider only when Volume is selected or always visible (choose selected)
        if selected == vol_index:
            # draw slider track
            pygame.draw.rect(screen, (100, 100, 100), slider_rect, border_radius=6)
            # draw filled part
            filled_rect = pygame.Rect(
                slider_x, slider_y, int(current_volume * slider_w), slider_h
            )
            pygame.draw.rect(screen, (170, 170, 170), filled_rect, border_radius=6)
            # draw handle
            pygame.draw.rect(screen, (240, 240, 240), handle_rect, border_radius=6)
            pygame.draw.rect(screen, (120, 120, 120), handle_rect, 2, border_radius=6)

            # percentage text near slider
            perc_font = pygame.font.Font(None, 24)
            perc_text = perc_font.render(
                f"{int(current_volume * 100)}%", True, (220, 220, 220)
            )
            screen.blit(perc_text, (slider_x + slider_w + 12, slider_y - 6))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, current_resolution, flags
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options_buttons)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options_buttons)
                elif event.key == pygame.K_RETURN:
                    if options_buttons[selected] == "Resolution":
                        current_index = possible_resolutions.index(current_resolution)
                        current_resolution = possible_resolutions[
                            (current_index + 1) % len(possible_resolutions)
                        ]
                        flags = pygame.FULLSCREEN if fullscreen else 0
                        screen = pygame.display.set_mode(current_resolution, flags)
                        pygame.display.flip()
                    elif options_buttons[selected] == "Fullscreen":
                        fullscreen = not fullscreen
                        flags = pygame.FULLSCREEN if fullscreen else 0
                        screen = pygame.display.set_mode(current_resolution, flags)
                        pygame.display.flip()
                    elif options_buttons[selected] == "Back":
                        return True, current_resolution, flags
                elif event.key == pygame.K_RIGHT:
                    # if volume selected, increase
                    if selected == vol_index:
                        current_volume = min(1.0, current_volume + 0.05)
                        try:
                            pygame.mixer.music.set_volume(current_volume)
                        except Exception:
                            pass
                elif event.key == pygame.K_LEFT:
                    if selected == vol_index:
                        current_volume = max(0.0, current_volume - 0.05)
                        try:
                            pygame.mixer.music.set_volume(current_volume)
                        except Exception:
                            pass

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if selected == vol_index and (
                    handle_rect.collidepoint((mx, my))
                    or slider_rect.collidepoint((mx, my))
                ):
                    dragging = True
                    # update immediately
                    rel_x = mx - slider_x
                    current_volume = max(0.0, min(1.0, rel_x / slider_w))
                    try:
                        pygame.mixer.music.set_volume(current_volume)
                    except Exception:
                        pass
                else:
                    # click on menu items (basic hit detection using text positions)
                    for i in range(len(options_buttons)):
                        item_rect = pygame.Rect(50, 50 + i * 50, 600, 40)
                        if item_rect.collidepoint((mx, my)):
                            selected = i
                            # emulate return press on click
                            if options_buttons[selected] == "Resolution":
                                current_index = possible_resolutions.index(
                                    current_resolution
                                )
                                current_resolution = possible_resolutions[
                                    (current_index + 1) % len(possible_resolutions)
                                ]
                                flags = pygame.FULLSCREEN if fullscreen else 0
                                screen = pygame.display.set_mode(
                                    current_resolution, flags
                                )
                                pygame.display.flip()
                            elif options_buttons[selected] == "Fullscreen":
                                fullscreen = not fullscreen
                                flags = pygame.FULLSCREEN if fullscreen else 0
                                screen = pygame.display.set_mode(
                                    current_resolution, flags
                                )
                                pygame.display.flip()
                            elif options_buttons[selected] == "Back":
                                return True, current_resolution, flags

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                mx, my = event.pos
                rel_x = mx - slider_x
                current_volume = max(0.0, min(1.0, rel_x / slider_w))
                try:
                    pygame.mixer.music.set_volume(current_volume)
                except Exception:
                    pass

    # fallback
    return True, current_resolution, flags
