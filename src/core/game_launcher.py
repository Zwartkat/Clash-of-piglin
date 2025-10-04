import pygame
import esper
import os

from core.camera import CAMERA
from components.effects import OnTerrain
from components.team import Team
from core.event_bus import EventBus
from core.services import Services
from enums.entity_type import EntityType
from events.resize_event import ResizeEvent
from events.spawn_unit_event import SpawnUnitEvent
from systems.collision_system import CollisionSystem
from systems.combat_system import CombatSystem
from systems.death_event_handler import DeathEventHandler
from systems.combat_system import CombatSystem
from systems.death_event_handler import DeathEventHandler
from systems.mouvement_system import MovementSystem
from components.position import Position
from systems.player_manager import PlayerManager
from systems.player_move_system import PlayerMoveSystem
from systems.render_system import RenderSystem
from systems.targeting_system import TargetingSystem
from components.case import Case
from components.map import Map
from systems.selection_system import SelectionSystem
from systems.terrain_effect_system import TerrainEffectSystem
from systems.economy_system import EconomySystem
from systems.entity_factory import EntityFactory
from systems.unit_factory import UnitFactory
from systems.input_manager import InputManager
from enums.case_type import CaseType
from core.config import Config
from systems.input_router_system import InputRouterSystem
from systems.quit_system import QuitSystem
from systems.camera_system import CameraSystem

tile_size = Config.TILE_SIZE()


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
                print(tile_size)
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

    info = pygame.display.Info()
    win_w, win_h = 800, 600

    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

    map_width, map_height = resize(screen, map_size)

    clock = pygame.time.Clock()

    # from ui.hud import HUDSystem

    # ui = HUDSystem(screen, hud_width)

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

    def on_resize(resize_event: ResizeEvent):
        resize(screen, 24)

    # Subscribes
    Services.event_bus = EventBus.get_event_bus()

    Services.event_bus.subscribe(ResizeEvent, on_resize)
    Services.event_bus.subscribe(SpawnUnitEvent, UnitFactory.create_unit_event)

    Services.event_bus.emit(
        SpawnUnitEvent(EntityType.GHAST, Team(1), Position(200, 700))
    )

    player_manager = PlayerManager(
        [
            Position(tile_size, tile_size),
            Position(map_width - tile_size, map_height - tile_size),
        ]
    )

    Services.player_manager = player_manager

    from config.units import UNITS

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
    event_bus_instance = EventBus.get_event_bus()
    world.add_processor(PlayerMoveSystem())
    world.add_processor(EconomySystem(event_bus_instance))
    death_handler = DeathEventHandler(event_bus_instance)
    world.add_processor(TargetingSystem())
    world.add_processor(CombatSystem())
    world.add_processor(CameraSystem(CAMERA))

    input_manager = InputManager()
    render = RenderSystem(screen, game_map, sprites)

    world.add_processor(input_manager)
    world.add_processor(render)
    world.add_processor(InputRouterSystem())

    # J'ai fait un dictionnaire pour que lorsque le quitsystem modifie la valeur, la valeur est modifiée dans ce fichier aussi
    game_state = {"running": True}

    world.add_processor(QuitSystem(event_bus_instance, game_state))

    while game_state["running"]:

        clock.tick(60)

        dt = min(clock.get_time() / 1000, dt)

        world.process(dt)  # dt = 1/60 pour 60 FPS

        # draw_map(screen,game_map,sprites)
        render.show_map()
        render.process(dt)
        selection_system.draw_selections(screen)

        # ui.draw()
        pygame.display.flip()

    pygame.quit()


def resize(screen: pygame.Surface, map_size: int) -> tuple[int]:

    hud_width = 100

    Config.tile_size = (screen.get_width() - hud_width * 2) / map_size
    print(Config.tile_size)

    map_width = Config.tile_size * map_size
    map_height = Config.tile_size * map_size

    screen_rect = screen.get_rect()

    CAMERA.set_size(screen_rect.width - (hud_width * 2) - 20, screen_rect.height)
    CAMERA.set_world_size(map_width, map_height)
    CAMERA.set_offset(hud_width + 10, 0)

    return map_width, map_height
