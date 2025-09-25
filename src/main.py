# src/main.py
import pygame
import esper
import os
from components.collider import Collider
from components.team import PLAYER_1_TEAM, PLAYER_2_TEAM, Team
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
from components.selection import Selection
from systems.selection_system import SelectionSystem
from components.effects import OnTerrain
from systems.terrain_effect_system import TerrainEffectSystem
from systems.player_manager import PlayerManager
from systems.unit_factory import UnitFactory
from ui.hud import Hud

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


# def load_hud_sprites():
#     """Charge tous les sprites utilisés par le hud."""
#     sprites = {}
#     asset_path = "assets/images/"

#     sprites_files = {"Gold_nugget": "Gold_nugget.png", "Clock": "Clock.png"}

#     for sprite_type, filename in sprites_files.items():
#         full_path = os.path.join(asset_path, filename)
#         if os.path.exists(full_path):
#             sprite = pygame.image.load(full_path)
#             sprite = pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))
#             sprites[sprite_type] = sprite
#         else:
#             print(f"Warning: Image not found: {full_path}")
#             # Créer un rectangle coloré de fallback
#             sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
#             fallback_color = (255, 255, 255)
#             sprite.fill(fallback_color)
#             sprites[sprite_type] = sprite

#     return sprites


def draw_map(screen, game_map, sprites):
    """Dessine la map à l'écran avec les vraies images"""
    for y in range(len(game_map.tab)):
        for x in range(len(game_map.tab[y])):
            tile_type = game_map.tab[y][x]

            # Récupérer le sprite correspondant
            sprite = sprites.get(tile_type.type, sprites.get("Netherrack"))

            # Position de la tile
            pos_x = x * TILE_SIZE
            pos_y = y * TILE_SIZE
            screen.blit(sprite, (pos_x, pos_y))


def display_current_player(screen, player_manager):
    """Affiche le joueur actuel en haut à gauche"""
    font = pygame.font.Font(None, 36)
    player_text = f"Joueur {player_manager.current_player}"
    color = (0, 255, 0) if player_manager.current_player == 1 else (255, 0, 0)
    text_surface = font.render(player_text, True, color)
    screen.blit(text_surface, (10, 10))

    # Instructions
    instruction_font = pygame.font.Font(None, 24)
    instruction_text = "Appuyez sur CTRL pour changer de joueur"
    instruction_surface = instruction_font.render(
        instruction_text, True, (255, 255, 255)
    )
    screen.blit(instruction_surface, (10, 50))
    
def add_hud(screen, time, offset: tuple[int]):
    """Ajoute/met à jour le hud de la fenêtre."""

    hud = Hud(time)
    hud.makeHud(screen, offset)
    # pygame.font.init()
    # font = pygame.font.SysFont(None, 32)  # None for default font, 32 for size

    # time_text: str = "Timer : "
    # money_text: str = "You currently have {money} gold."

    # text_surface_timer = font.render(time_text, True, (255, 255, 255))  # White color
    # time_surface = font.render(str(time), True, (255, 255, 255))
    # text_surface_money = font.render(money_text, True, (255, 255, 255))  # White color
    # money_surface = font.render(str(money), True, (255, 255, 255))

    # screen.blit(sprites.get("Clock"), (offset[0], offset[1]))
    # screen.blit(text_surface_timer, (offset[0], offset[1] + 50))
    # screen.blit(time_surface, (offset[0], offset[1] + 100))
    # screen.blit(sprites.get("Gold_nugget"), (offset[0], offset[1] + 150))
    # screen.blit(text_surface_money, (offset[0], offset[1] + 200))
    # screen.blit(money_surface, (offset[0], offset[1] + 250))


pygame.init()
map_width = 24 * TILE_SIZE
map_height = 24 * TILE_SIZE
hud_width = 0.4*map_width
clock = pygame.time.Clock()
screen = pygame.display.set_mode((map_width + hud_width, map_height)) #map_width + hud_width, 
pygame.display.set_caption("Clash of Piglin - 2 Joueurs")

# Charger la map et les sprites
game_map = Map()
game_map.setTab(tab)
sprites = load_terrain_sprites()

# Créer le gestionnaire de joueurs
player_manager = PlayerManager()

# Creer le hud et charger ses textures
# sprites_hud = load_hud_sprites()

# Crée le monde Esper
world = esper
world.add_processor(MovementSystem())
world.add_processor(TerrainEffectSystem(game_map))
world.add_processor(CollisionSystem(game_map))

# Créer le système de sélection avec le gestionnaire de joueurs
selection_system = SelectionSystem(player_manager)

# === CRÉATION DES UNITÉS JOUEUR 1 ===

# Escouade d'épéistes Joueur 1
sword_positions_p1 = [(150, 150), (180, 150), (120, 150)]
sword_squad_p1 = UnitFactory.create_squad(
    "piglin_sword", sword_positions_p1, PLAYER_1_TEAM
)

# Escouade d'arbalétriers Joueur 1
crossbow_positions_p1 = [(150, 250), (180, 250), (210, 250)]
crossbow_squad_p1 = UnitFactory.create_squad(
    "piglin_crossbow", crossbow_positions_p1, PLAYER_1_TEAM
)

# Ghast Joueur 1
ghast_p1 = UnitFactory.create_unit("ghast", 250, 350, PLAYER_1_TEAM)

# === CRÉATION DES UNITÉS JOUEUR 2 ===

# Escouade d'épéistes Joueur 2
sword_positions_p2 = [(550, 150), (580, 150), (520, 150)]
sword_squad_p2 = UnitFactory.create_squad(
    "piglin_sword", sword_positions_p2, PLAYER_2_TEAM
)

# Escouade d'arbalétriers Joueur 2
crossbow_positions_p2 = [(550, 250), (580, 250), (610, 250)]
crossbow_squad_p2 = UnitFactory.create_squad(
    "piglin_crossbow", crossbow_positions_p2, PLAYER_2_TEAM
)

# Ghast Joueur 2
ghast_p2 = UnitFactory.create_unit("ghast", 450, 350, PLAYER_2_TEAM)

# Crée l'EventBus et le système de déplacement joueur
event_bus_instance = event_bus.EventBus()
world.add_processor(PlayerMoveSystem(event_bus_instance))

mouse_pressed = False
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            # Changement de joueur avec CTRL
            if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                player_manager.switch_player()
                selection_system.clear_selection(world)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche - sélection
                mouse_pressed = True
                selection_system.handle_mouse_down(event.pos, world)

            elif event.button == 3:  # Clic droit - donner ordre aux sélectionnées
                selected_entities = selection_system.get_selected_entities(world)
                if selected_entities:
                    x, y = event.pos

                    # Formation des troupes
                    from systems.troop_system import FormationSystem, TROOP_GRID

                    positions = FormationSystem.calculate_formation_positions(
                        selected_entities, x, y, spacing=35, formation_type=TROOP_GRID
                    )

                    # Donner les ordres de mouvement
                    for i, ent in enumerate(selected_entities):
                        if i < len(positions):
                            target_x, target_y = positions[i]
                            event_bus_instance.emit(
                                EventMoveTo(ent, target_x, target_y)
                            )

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Relâcher clic gauche
                mouse_pressed = False
                selection_system.handle_mouse_up(event.pos, world)

        elif event.type == pygame.MOUSEMOTION:
            if mouse_pressed:
                selection_system.handle_mouse_motion(event.pos, world)

    # Traitement des systèmes
    world.process(1 / 60)  # dt = 1/60 pour 60 FPS

    # Affichage
    screen.fill((0, 0, 0))  # fond noir

    # Dessiner la map
    draw_map(screen, game_map, sprites)

    # Dessiner les entités (avec couleurs d'équipe)
    # ajoute le hud
    add_hud(screen, clock.get_time(), (map_width, 0))

    # Le SelectionSystem gère maintenant TOUT l'affichage des entités
    selection_system.draw_selections(screen, world)

    # Afficher le joueur actuel
    display_current_player(screen, player_manager)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
