import pygame
import esper
import os
from components.collider import Collider
from components.team import PLAYER_TEAM, Team
from core import event_bus
from events.event_move import EventMoveTo
from systems.collision_system import CollisionSystem
from systems.mouvement_system import MovementSystem
from components.position import Position
from components.velocity import Velocity
from systems.player_move_system import PlayerMoveSystem
from temp_map import tab
from components.case import Case
from components.map import Map

TILE_SIZE = 32


def load_terrain_sprites():
    """Charge tous les sprites de terrain"""
    sprites = {}
    asset_path = "assets/images/"

    terrain_files = {
        "Netherrack": "Netherrack.png",
        "Blue_netherrack": "Blue_netherrack.png",
        "Red_netherrack": "Red_netherrack.png",
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
    printed_types = set()  # Pour éviter de spam la console

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
map_width = 24 * TILE_SIZE
map_height = 24 * TILE_SIZE
screen = pygame.display.set_mode((map_width, map_height))
clock = pygame.time.Clock()

# Charger la map et les sprites
game_map = Map()
game_map.setTab(tab)
sprites = load_terrain_sprites()

# Crée le monde Esper
world = esper
world.add_processor(MovementSystem())
world.add_processor(CollisionSystem(game_map))
# Crée l'entité et ses composants
entity = world.create_entity()
world.add_component(entity, Position(x=100, y=200))
world.add_component(entity, Velocity(x=0, y=0))
world.add_component(entity, Team(PLAYER_TEAM))

entity2 = world.create_entity()
world.add_component(entity2, Position(x=200, y=300))
world.add_component(entity2, Velocity(x=0, y=0))
world.add_component(entity2, Team(PLAYER_TEAM))

entity3 = world.create_entity()
world.add_component(entity3, Position(x=300, y=400))
world.add_component(entity3, Velocity(x=0, y=0))
world.add_component(entity3, Team(PLAYER_TEAM))

entity4 = world.create_entity()
world.add_component(entity4, Position(x=400, y=500))
world.add_component(entity4, Velocity(x=0, y=0))
world.add_component(entity4, Team(PLAYER_TEAM))

world.add_component(entity, Collider(width=20, height=20, collision_type="player"))
world.add_component(entity2, Collider(width=20, height=20, collision_type="player"))
world.add_component(entity3, Collider(width=20, height=20, collision_type="player"))
world.add_component(entity4, Collider(width=20, height=20, collision_type="player"))

# Crée l'EventBus et le système de déplacement joueur
event_bus_instance = event_bus.EventBus()
world.add_processor(MovementSystem())
world.add_processor(PlayerMoveSystem(event_bus_instance))
world.add_processor(CollisionSystem(game_map))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            for ent, (pos, vel, team) in world.get_components(Position, Velocity, Team):
                if team.team_id == PLAYER_TEAM:
                    event_bus_instance.emit(EventMoveTo(ent, x, y))

    world.process(1 / 60)  # dt = 1/60 pour 60 FPS

    screen.fill((0, 0, 0))  # fond noir

    # Dessiner la map d'abord
    draw_map(screen, game_map, sprites)

    # Puis dessine les entités par-dessus
    for ent, pos in world.get_component(Position):
        # Récupérer le collider pour connaître la taille
        collider = world.component_for_entity(ent, Collider)

        if collider:
            # Calculer la position du rectangle (coin supérieur gauche)
            rect_x = int(pos.x - collider.width / 2)
            rect_y = int(pos.y - collider.height / 2)

            # Dessiner un rectangle rouge de la taille de l'hitbox
            rect = pygame.Rect(rect_x, rect_y, collider.width, collider.height)
            pygame.draw.rect(screen, (255, 0, 0), rect)

        else:
            # Fallback si pas de collider (dessiner un petit carré)
            pygame.draw.rect(
                screen, (255, 0, 0), (int(pos.x - 5), int(pos.y - 5), 10, 10)
            )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
