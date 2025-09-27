import pygame
import esper
import os
from components.collider import Collider
from components.team import PLAYER_1_TEAM, Team
from core import event_bus
from events.event_move import EventMoveTo
from systems.collision_system import CollisionSystem
from systems.mouvement_system import MovementSystem
from components.position import Position
from components.velocity import Velocity
from systems.player_manager import PlayerManager
from components.money import Money
from components.squad import Squad
from systems.player_move_system import PlayerMoveSystem
from systems.render_system import RenderSystem
from temp_map import tab
from components.case import Case
from components.map import Map
from components.selection import Selection
from systems.selection_system import SelectionSystem
from components.effects import OnTerrain
from systems.terrain_effect_system import TerrainEffectSystem
from systems.unit_factory import UnitFactory
from systems.economy_system import EconomySystem
from systems.entity_factory import EntityFactory
from config.constants import CaseType

TILE_SIZE = 32


def load_terrain_sprites():
    """Charge tous les sprites de terrain"""

    # TODO :
    # Modifier pour utiliser core.config.Config pour récupérer les path (actuellement bugué)

    sprites = {}
    asset_path = "assets/images/"

    terrain_files = {
        CaseType.NETHERRACK: "Netherrack.png",
        CaseType.BLUE_NETHERRACK: "Blue_netherrack.png",
        CaseType.RED_NETHERRACK: "Red_netherrack.png",
        CaseType.SOULSAND: "Soulsand.png",
        CaseType.LAVA: "Lava.png",
    }

    for terrain_type, filename in terrain_files.items():
        full_path = os.path.join(asset_path, filename)
        if os.path.exists(full_path):
            sprite = pygame.image.load(full_path)
            if terrain_type != CaseType.LAVA:
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


def draw_map(screen, game_map: Map, sprites):
    """Dessine la map à l'écran avec les vraies images"""
    printed_types = set()  # Pour éviter de spam la console

    for y in range(len(game_map.tab)):
        for x in range(len(game_map.tab[y])):
            tile_type: Case = game_map.tab[y][x].getType()

            # Récupérer le sprite correspondant
            sprite = sprites.get(tile_type, sprites.get(CaseType.NETHERRACK))

            if tile_type.type != CaseType.LAVA:

                # Position de la tile
                pos_x = x * TILE_SIZE
                pos_y = y * TILE_SIZE

            # Dessiner le sprite
            screen.blit(sprite, (pos_x, pos_y))


def main(screen: pygame.Surface):

    dt = 0.05
    map_width = 24 * TILE_SIZE
    map_height = 24 * TILE_SIZE
    screen = pygame.display.set_mode((map_width, map_height))
    clock = pygame.time.Clock()

    # Charger la map et les sprites
    game_map = Map()
    # game_map.setTab(tab)
    game_map.generate(24)
    sprites = load_terrain_sprites()

    for y in range(len(game_map.tab)):
        for x in range(len(game_map.tab[y])):
            tile_type = game_map.tab[y][x]

            if tile_type.type == CaseType.LAVA:
                case = Case(Position(x * TILE_SIZE, y * TILE_SIZE), CaseType.LAVA)
                EntityFactory.create(*case.get_all_components())

        # Crée l'entité et ses composants
    # sword_positions = [(200, 200), (230, 200), (160, 200)]
    # sword_squad = UnitFactory.create_squad(
    #    "piglin_sword", sword_positions, PLAYER_1_TEAM
    # )
    #
    ## Escouade d'Arbalétriers
    # crossbow_positions = [(200, 300), (230, 300), (260, 300)]
    # crossbow_squad = UnitFactory.create_squad(
    #    "piglin_crossbow", crossbow_positions, PLAYER_1_TEAM
    # )

    # Ghast solitaire
    # ghast = UnitFactory.create_unit("ghast", 350, 400, PLAYER_1_TEAM)

    from entities.crossbowman import Crossbowman
    from entities.brute import Brute
    from entities.ghast import Ghast

    EntityFactory.create(*Crossbowman().get_all_components())
    EntityFactory.create(*Ghast().get_all_components())
    EntityFactory.create(*Brute().get_all_components())

    # Crée le monde Esper
    world = esper
    world.add_processor(MovementSystem())
    world.add_processor(TerrainEffectSystem(game_map))
    world.add_processor(CollisionSystem(game_map))
    selection_system = SelectionSystem(PlayerManager())

    # Crée l'EventBus et le système de déplacement joueur
    event_bus_instance = event_bus.EventBus.get_event_bus()
    world.add_processor(PlayerMoveSystem(event_bus_instance))
    world.add_processor(EconomySystem(event_bus_instance))

    # Création d'un player avec ses thunes et sa team
    # EntityFactory.create(Money(600), Squad(sword_squad + crossbow_squad + [ghast]))

    render = RenderSystem(screen, game_map.tab, sprites)

    event_bus_instance.subscribe(EventMoveTo, render.animate_move)

    mouse_pressed = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche - sélection
                    mouse_pressed = True
                    selection_system.handle_mouse_down(event.pos, world)
                elif event.button == 3:  # Clic droit - donner ordre aux sélectionnées
                    selected_entities = selection_system.get_selected_entities(world)
                    if selected_entities:
                        x, y = event.pos
                        from systems.troop_system import (
                            FormationSystem,
                            TROOP_GRID,
                            TROOP_CIRCLE,
                        )

                        positions = FormationSystem.calculate_formation_positions(
                            selected_entities,
                            x,
                            y,
                            spacing=35,
                            formation_type=TROOP_GRID,  # you can change to TROOP_CIRCLE if needed
                        )

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

        clock.tick(100)

        dt = min(clock.get_time() / 1000, dt)

        world.process(dt)  # dt = 1/60 pour 60 FPS

        # draw_map(screen,game_map,sprites)
        render.show_map()
        render.process(dt)
        selection_system.draw_selections(screen, world)
        pygame.display.flip()

    pygame.quit()
