import pygame
import esper
from core.config import Config
import core.game_launcher as game_launcher

if __name__ == "__main__":
    Config.load()
    pygame.init()
    pygame.display.set_caption(Config.get(key="game_name"))
    screen = pygame.display.set_mode((800, 600))
    game_launcher.main(screen)
