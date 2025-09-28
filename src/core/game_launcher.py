import pygame
import esper
import os

from core.camera import CAMERA
from components.effects import OnTerrain
from components.team import Team
from components.velocity import Velocity
from core import event_bus
from core.entity import Entity
from events.event_move import EventMoveTo
from systems.collision_system import CollisionSystem
from systems.combat_system import CombatSystem
from systems.death_event_handler import DeathEventHandler
from systems.combat_system import CombatSystem
from systems.death_event_handler import DeathEventHandler
from systems.mouvement_system import MovementSystem
from components.position import Position
from systems.player_manager import PlayerManager
from components.money import Money
from components.squad import Squad
from systems.player_move_system import PlayerMoveSystem
from systems.render_system import RenderSystem
from systems.targeting_system import TargetingSystem
from components.case import Case
from components.map import Map
from systems.selection_system import SelectionSystem
from systems.terrain_effect_system import TerrainEffectSystem
from systems.economy_system import EconomySystem
from systems.entity_factory import EntityFactory
from enums.case_type import CaseType
from core.config import Config

tile_size: int = Config.TILE_SIZE()


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
                sprite = pygame.transform.scale(sprite, (tile_size, tile_size))
                sprites[terrain_type] = sprite

        else:
            print(f"Warning: Image not found: {full_path}")
            sprite = pygame.Surface((tile_size, tile_size))
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


def main(screen: pygame.Surface, map_size=24):

    dt = 0.05
    map_width = map_size * tile_size
    map_height = map_size * tile_size
    screen = pygame.display.set_mode((800, 700))
    clock = pygame.time.Clock()

    screen_rect = screen.get_rect()

    CAMERA.set_size(screen_rect.width, screen_rect.height)
    CAMERA.set_world_size(map_width, map_height)

    # Charger la map et les sprites
    game_map: Map = Map()
    game_map.generate(map_size)
    sprites = load_terrain_sprites()

    for y in range(len(game_map.tab)):
        for x in range(len(game_map.tab[y])):
            tile_type = game_map.tab[y][x]

            if tile_type.type == CaseType.LAVA:
                case = Case(Position(x * tile_size, y * tile_size), CaseType.LAVA)
                EntityFactory.create(*case.get_all_components())

    player_manager = PlayerManager()

    from config.units import UNITS
    from enums.entity_type import EntityType
    from systems.unit_factory import UnitFactory

    entities_1 = []

    for i in range(6):

        entities_1.append(
            UnitFactory.create_unit(EntityType.GHAST, Team(1), Position(200, 400))
        )
    for i in range(6):

        entities_1.append(
            UnitFactory.create_unit(EntityType.CROSSBOWMAN, Team(1), Position(200, 300))
        )
    for i in range(6):
        entities_1.append(
            UnitFactory.create_unit(EntityType.BRUTE, Team(1), Position(200, 500))
        )

    entities_2 = []

    entities_2.append(
        EntityFactory.create(
            *UNITS[EntityType.CROSSBOWMAN].get_all_components(),
            Position(100, 200),
            Team(2),
            OnTerrain(),
        )
    )
    entities_2.append(
        EntityFactory.create(
            *UNITS[EntityType.GHAST].get_all_components(),
            Position(300, 200),
            Team(2),
            OnTerrain(),
        )
    )
    entities_2.append(
        EntityFactory.create(
            *UNITS[EntityType.BRUTE].get_all_components(),
            Position(400, 100),
            Team(2),
            OnTerrain(),
        )
    )
    #
    # Crée le monde Esper
    world = esper
    world.add_processor(MovementSystem())
    world.add_processor(TerrainEffectSystem(game_map))
    world.add_processor(CollisionSystem(game_map))
    selection_system = SelectionSystem(player_manager)

    # Crée l'EventBus et le système de déplacement joueur
    event_bus_instance = event_bus.EventBus.get_event_bus()
    world.add_processor(PlayerMoveSystem(event_bus_instance))
    world.add_processor(EconomySystem(event_bus_instance))
    death_handler = DeathEventHandler(event_bus_instance)
    world.add_processor(TargetingSystem())
    world.add_processor(CombatSystem())
    # Création d'un player avec ses thunes et sa team

    EntityFactory.create(Money(600), Squad(entities_1), Team(1))
    EntityFactory.create(Money(600), Squad(entities_2), Team(2))

    render = RenderSystem(screen, game_map, sprites)

    world.add_processor(render)

    event_bus_instance.subscribe(EventMoveTo, render.animate_move)

    mouse_pressed = False

    keys_down = {
        pygame.K_UP: False,
        pygame.K_DOWN: False,
        pygame.K_RIGHT: False,
        pygame.K_LEFT: False,
    }

    running = True
    while running:

        ###################################################################################
        # To move (Check https://trello.com/c/X1GHv5GY)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Changement de joueur avec CTRL
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    player_manager.switch_player()
                    selection_system.clear_selection(world)

                if event.key == pygame.K_UP:
                    keys_down[pygame.K_UP] = True
                if event.key == pygame.K_DOWN:
                    keys_down[pygame.K_DOWN] = True
                if event.key == pygame.K_LEFT:
                    keys_down[pygame.K_LEFT] = True
                if event.key == pygame.K_RIGHT:
                    keys_down[pygame.K_RIGHT] = True
                if event.key == pygame.K_SPACE:
                    CAMERA.set_position(0, 0)
                    CAMERA.set_zoom(1.0)

            elif event.type == pygame.KEYUP:

                if event.key == pygame.K_UP:
                    keys_down[pygame.K_UP] = False
                if event.key == pygame.K_DOWN:
                    keys_down[pygame.K_DOWN] = False
                if event.key == pygame.K_LEFT:
                    keys_down[pygame.K_LEFT] = False
                if event.key == pygame.K_RIGHT:
                    keys_down[pygame.K_RIGHT] = False

            elif event.type == pygame.MOUSEWHEEL:
                CAMERA.zoom(0.05 * event.y)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche - sélection
                    mouse_pressed = True
                    selection_system.handle_mouse_down(
                        CAMERA.unapply(event.pos[0], event.pos[1]), world
                    )
                elif event.button == 3:  # Clic droit - donner ordre aux sélectionnées
                    selected_entities = selection_system.get_selected_entities(world)
                    if selected_entities:
                        x, y = CAMERA.unapply(event.pos[0], event.pos[1])
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

                    selection_system.handle_mouse_up(
                        CAMERA.unapply(event.pos[0], event.pos[1]), world
                    )
            elif event.type == pygame.MOUSEMOTION:
                if mouse_pressed:
                    selection_system.handle_mouse_motion(
                        CAMERA.unapply(event.pos[0], event.pos[1]), world
                    )

        if keys_down[pygame.K_UP]:
            CAMERA.move(0, -5)
        if keys_down[pygame.K_DOWN]:
            CAMERA.move(0, 5)
        if keys_down[pygame.K_LEFT]:
            CAMERA.move(-5, 0)
        if keys_down[pygame.K_RIGHT]:
            CAMERA.move(5, 0)

        ###################################################################################

        clock.tick(60)

        dt = min(clock.get_time() / 1000, dt)

        world.process(dt)  # dt = 1/60 pour 60 FPS

        # draw_map(screen,game_map,sprites)
        render.show_map()
        render.process(dt)
        selection_system.draw_selections(screen, world)
        display_current_player(screen, player_manager)
        display_current_player(screen, player_manager)
        pygame.display.flip()

    pygame.quit()
