import pygame
import esper
import os
from core import event_bus
from events.event_move import EventMoveTo
from systems.mouvement_system import MovementSystem
from components.position import Position
from components.velocity import Velocity
from systems.player_move_system import PlayerMoveSystem
from temp_map import tab

# Import des classes Map depuis le répertoire components (comme dans test_map_display)
from components.case import Case
from components.map import Map

TILE_SIZE = 32


def load_terrain_sprites():
    """Charge tous les sprites de terrain"""
    sprites = {}
    asset_path = "assets/images/"

    # Mapping CORRIGÉ avec les bonnes images
    terrain_files = {
        "Netherrack": "Netherrack.png",
        "Blue_netherrack": "Blue_netherrack.png",  # ← Corrigé !
        "Red_netherrack": "Red_netherrack.png",  # ← Corrigé !
        "Lava": "Lava_long.png",
        "Soulsand": "Soul_Sand.png",
    }

    for terrain_type, filename in terrain_files.items():
        full_path = os.path.join(asset_path, filename)
        if os.path.exists(full_path):
            sprite = pygame.image.load(full_path)
            sprite = pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))
            sprites[terrain_type] = sprite
        else:
            print(f"Warning: Image not found: {full_path}")
            # Créer un rectangle coloré de fallback
            sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
            fallback_colors = {
                "Netherrack": (139, 69, 19),
                "Blue_netherrack": (100, 150, 255),
                "Red_netherrack": (255, 100, 100),
                "Lava": (255, 100, 0),
                "Soulsand": (101, 67, 33),
            }
            sprite.fill(fallback_colors.get(terrain_type, (128, 128, 128)))
            sprites[terrain_type] = sprite

    return sprites


def draw_map(screen, game_map, sprites):
    """Dessine la map à l'écran avec les vraies images"""
    for y in range(len(game_map.tab)):
        for x in range(len(game_map.tab[y])):
            tile_type = game_map.tab[y][x]

            # Récupérer le sprite correspondant
            sprite = sprites.get(tile_type, sprites.get("Netherrack"))

            # Position de la tile
            pos_x = x * TILE_SIZE
            pos_y = y * TILE_SIZE

            # Dessiner le sprite
            screen.blit(sprite, (pos_x, pos_y))


pygame.init()
# Correction : 24x24 au lieu de 25x25
map_width = 24 * TILE_SIZE  # 24 * 32 = 768
map_height = 24 * TILE_SIZE  # 24 * 32 = 768
screen = pygame.display.set_mode((map_width, map_height))
clock = pygame.time.Clock()

# Charger la map et les sprites
game_map = Map()
game_map.setTab(tab)
sprites = load_terrain_sprites()

# Crée le monde Esper
world = esper
world.add_processor(MovementSystem())

# Crée l'entité et ses composants
entity = world.create_entity()
world.add_component(entity, Position(x=100, y=200))
world.add_component(entity, Velocity(x=0, y=0))

entity2 = world.create_entity()
world.add_component(entity2, Position(x=200, y=300))
world.add_component(entity2, Velocity(x=0, y=0))

# Crée l'EventBus et le système de déplacement joueur
event_bus_instance = event_bus.EventBus()
player_move_system = PlayerMoveSystem(event_bus_instance)
world.add_processor(player_move_system)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            event_bus_instance.emit(EventMoveTo(entity, x, y))
            event_bus_instance.emit(EventMoveTo(entity2, x, y))

    world.process(1 / 60)  # dt = 1/60 pour 60 FPS

    screen.fill((0, 0, 0))  # fond noir

    # Dessiner la map d'abord
    draw_map(screen, game_map, sprites)

    # Puis dessiner les entités par-dessus
    for ent, pos in world.get_component(Position):
        pygame.draw.circle(screen, (255, 0, 0), (int(pos.x), int(pos.y)), 10)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
