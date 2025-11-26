import pygame, time

from core.game.timer import Timer


class Notification:
    def __init__(self, text, duration=2500, color=(255, 255, 255), hud_size=100):
        self.text = text
        self.duration = duration
        self.color = color
        self.timer = Timer("notification")
        self.alpha = 255
        self.font = pygame.font.SysFont("consolas", 15)
        self.text_surface = self.render_wrapped_text(text, color, hud_size - 30)
        self.bg = pygame.Surface(
            (self.text_surface.get_width() + 20, self.text_surface.get_height() + 12),
            pygame.SRCALPHA,
        )
        self.bg_rect = self.bg.get_rect(
            bottomright=(pygame.display.get_surface().get_width() - 10, 0)
        )

    def draw(self, surface: pygame.Surface, index=0):
        fade = max(
            0, 1 - (self.timer.elapsed_ms() / self.duration)
        )  # fraction entre 0 et 1
        self.alpha = int(255 * fade)
        if self.alpha <= 0 or index > 5:
            return False  # signal de suppression

        # position (empilement vertical si plusieurs notifs)
        self.bg_rect.bottom = (
            surface.get_height() - 20 - index * (self.bg_rect.height + 10)
        )

        # surface semi-transparente
        bg = self.bg.copy()
        bg.fill((20, 20, 20, self.alpha))
        pygame.draw.rect(bg, (0, 0, 0, self.alpha), bg.get_rect(), 2, border_radius=6)
        txt = self.text_surface.copy()
        txt.set_alpha(self.alpha)
        bg.blit(txt, (10, 6))
        surface.blit(bg, self.bg_rect)
        return True

    def render_wrapped_text(self, text, color, max_width):
        words = text.split(" ")
        lines = []
        current = ""

        for w in words:
            test = current + (" " if current else "") + w
            test_surface = self.font.render(test, True, color)

            if test_surface.get_width() <= max_width:
                current = test
            else:
                lines.append(current)
                current = w

        if current:
            lines.append(current)

        # créer la surface finale
        line_surfaces = [self.font.render(line, True, color) for line in lines]
        total_height = (
            sum(ls.get_height() for ls in line_surfaces) + (len(lines) - 1) * 2
        )

        surf = pygame.Surface((max_width, total_height), pygame.SRCALPHA)

        y = 0
        for ls in line_surfaces:
            surf.blit(ls, (0, y))
            y += ls.get_height() + 2

        return surf
