from core.entity import Entity
from core.player import Player
import pygame
import os
# from ..entities.brute import Brute
# from ..entities.crossbowman import Crossbowman
# from ..entities.ghast import Ghast


class Hud:
    
    allowed_troops : list[Entity] = [] #[Brute(), Crossbowman(), Ghast()]  # brute, crossbowman, ghast
    
    # pour chaque joueur : gold, troops(nombres&types), hp_bastion, generation 
    # general : timer

    def __init__(self, timer=0, players : list[Player] = []):
        self.timer = timer
        self.players = players[:2]
        
    def load_images(self, longueur) :
        
        sprites = {}
        asset_path = "./assets/images/"

        sprites_files = {"Gold_nugget": "Gold_nugget.png", "Clock": "Clock.png"}

        for sprite_type, filename in sprites_files.items():
            full_path = os.path.join(asset_path, filename)
            if os.path.exists(full_path):
                sprite = pygame.image.load(full_path)
                sprite = pygame.transform.scale(sprite, (longueur*0.08, longueur*0.08))
                sprites[sprite_type] = sprite
            else:
                print(f"Warning: Image not found: {full_path}")
                # Créer un rectangle coloré de fallback
                sprite = pygame.Surface((longueur*0.08, longueur*0.08))
                fallback_color = (255, 255, 255)
                sprite.fill(fallback_color)
                sprites[sprite_type] = sprite
                
        return sprites
        
    def makeHud(self, screen, dimensions_ecran : list[int]) :
        
        starting_point = [0, dimensions_ecran[1]]
        largeur = dimensions_ecran[0] * 0.4
        longueur = dimensions_ecran[1]
        
        limit_screen_1 = round(0.3*longueur)
        limit_screen_2 = round(0.65*longueur)
        limit_screen_3 = longueur
        
        images = self.load_images(longueur)
        
        screen.blit(images.get("Gold_nugget"), (starting_point[0], starting_point[1]))
        screen.blit(images.get("Clock"), (starting_point[0] + 0.20*largeur, starting_point[1] + 0.05*longueur))
        
        