import pygame, time

from core.game.timer import Timer


class Notification:
    def __init__(self, text, duration=2500, color=(255, 255, 255)):
        self.text = text
        self.duration = duration
        self.color = color
        self.timer = Timer("notification")
        self.alpha = 255
        self.font = pygame.font.SysFont("consolas", 20)
        self.text_surface = self.font.render(text, True, color)
        self.bg = pygame.Surface(
            (self.text_surface.get_width() + 20, self.text_surface.get_height() + 12),
            pygame.SRCALPHA,
        )
        self.bg_rect = self.bg.get_rect(
            center=(pygame.display.get_surface().get_width() // 2, 80)
        )

    def draw(self, surface, index=0):
        fade = max(
            0, 1 - (self.timer.elapsed_ms() / self.duration)
        )  # fraction entre 0 et 1
        self.alpha = int(255 * fade)
        if self.alpha <= 0:
            return False  # signal de suppression

        # position (empilement vertical si plusieurs notifs)
        self.bg_rect.y = 80 + index * (self.bg_rect.height + 10)

        # surface semi-transparente
        bg = self.bg.copy()
        bg.fill((20, 20, 20, self.alpha))
        pygame.draw.rect(bg, (0, 0, 0, self.alpha), bg.get_rect(), 2, border_radius=6)
        txt = self.text_surface.copy()
        txt.set_alpha(self.alpha)
        bg.blit(txt, (10, 6))
        surface.blit(bg, self.bg_rect)
        return True
