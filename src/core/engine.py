import importlib
import pygame
import esper
import os

from ai.world_perception import WorldPerception
from components.gameplay.attack import Attack
from config.ai_mapping import IA_MAP_JCJ
from core.data_bus import DATA_BUS
from core.accessors import (
    get_camera,
    get_config,
    get_entity,
    get_event_bus,
    get_notification_manager,
    get_player_manager,
)
from core.game.camera import CAMERA
from core.game.timer import Timer
from enums.config_key import ConfigKey
from enums.data_bus_key import DataBusKey
from enums.entity.entity_type import EntityType
from events.loading_events import (
    LoadingProgressEvent,
    LoadingStartEvent,
    LoadingFinishEvent,
)
from events.resize_event import ResizeEvent
from events.spawn_unit_event import SpawnUnitEvent
from systems.ai_system import AiSystem
from systems.sound_system import SoundSystem
from systems.world.collision_system import CollisionSystem
from systems.combat.combat_system import CombatSystem
from systems.lova_ai_system import LOVAAiSystem
from systems.pathfinding_system import PathfindingSystem
from systems.death_event_handler import DeathEventHandler
from systems.combat.combat_system import CombatSystem
from systems.death_event_handler import DeathEventHandler
from systems.world.movement_system import MovementSystem
from components.base.position import Position
from core.game.player_manager import PlayerManager
from systems.world.player_move_system import PlayerMoveSystem
from systems.rendering.render_system import RenderSystem
from systems.combat.targeting_system import TargetingSystem
from components.case import Case
from core.game.map import Map
from systems.input.selection_system import SelectionSystem
from systems.world.terrain_effect_system import TerrainEffectSystem
from systems.world.economy_system import EconomySystem
from factories.entity_factory import EntityFactory
from factories.unit_factory import UnitFactory
from core.input.input_manager import InputManager
from enums.case_type import CaseType
from core.config import Config
from systems.input.input_router_system import InputRouterSystem
from systems.quit_system import QuitSystem
from systems.input.camera_system import CameraSystem
from ui.hud_manager import HudManager
from systems.victory_system import VictorySystem
from systems.combat.arrow_system import ArrowSystem
from systems.scpr_ai_system import SCPRAISystem

# Import debug systems
from systems.debug_system import DebugRenderSystem
from systems.debug_event_handler import DebugEventHandler
from ui.loading import LoadingUISystem
from ui.notification_manager import NotificationManager
from ui.pause_menu import PauseMenuSystem
from events.pause_events import QuitToMenuEvent


def load_terrain_sprites(tile_size: int) -> dict[CaseType, pygame.Surface]:
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


def main(screen: pygame.Surface, map_size=24, ia_mode="jcia"):
    """
    args ia_mode: "jcia" pour Joueur contre IA, "iacia" pour IA contre IA
    """

    global game_state

    reset()

    # Reset game state at the start
    dt = 0.05

    win_w, win_h = 1200, 900

    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

    clock = pygame.time.Clock()

    # Crée le monde Esper
    world = esper
    font = pygame.font.Font(Config.get_assets(key="font"), 18)
    loading_system = LoadingUISystem(screen, font)

    def update_loading(progress: float, message: str):
        event_bus = get_event_bus()
        event_bus.emit(LoadingProgressEvent(progress, message))

        # Petit délai pour laisser l'animation se jouer
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 16:  # ~60 FPS
            dt = clock.tick(60) / 1000.0  # Delta time en secondes
            loading_system.process(dt)  # Utiliser le vrai dt, pas 0
            pygame.display.flip()
            pygame.event.pump()  # Garde la fenêtre responsive

    # === DÉBUT DU CHARGEMENT ===
    get_event_bus().emit(LoadingStartEvent("Initializing game..."))
    update_loading(0.0, "Initializing game...")

    # Charger la map
    update_loading(0.2, "Generating map...")
    map: Map = Map()
    map.generate(map_size)
    DATA_BUS.register(DataBusKey.MAP, map)
    DATA_BUS.register(DataBusKey.CAMERA, CAMERA)

    update_loading(0.4, "Loading sprites...")
    tile_size: int = DATA_BUS.get(DataBusKey.CONFIG).get(ConfigKey.TILE_SIZE, 32)
    sprites = load_terrain_sprites(tile_size)
    game_hud = HudManager(screen)

    update_loading(0.5, "Rendering map...")
    map_width, map_height = resize(screen, map_size, game_hud.hud.hud_width)

    from config.ai_mapping import IA_MAP

    if ia_mode == "iacia":
        DATA_BUS.register(DataBusKey.IA_MAPPING, IA_MAP)
    elif ia_mode == "jcia":
        DATA_BUS.register(DataBusKey.IA_MAPPING, IA_MAP_JCJ)

    for y in range(len(map.tab)):
        for x in range(len(map.tab[y])):
            tile_type = map.tab[y][x]

            if tile_type.type == CaseType.LAVA:
                case = Case(Position(x * tile_size, y * tile_size), CaseType.LAVA)
                EntityFactory.create(*case.get_all_components())

    def on_resize(resize_event: ResizeEvent):
        resize(screen, 24, game_hud.hud.hud_width)

    # Subscribes

    get_event_bus().subscribe(ResizeEvent, on_resize)
    get_event_bus().subscribe(SpawnUnitEvent, UnitFactory.create_unit_event)

    case_size = get_config().get(ConfigKey.TILE_SIZE, 32)

    # Initialiser les joueurs
    update_loading(0.6, "Initializing players...")

    player_manager = PlayerManager()

    DATA_BUS.register(DataBusKey.PLAYER_MANAGER, player_manager)

    # Charger les systèmes principaux
    update_loading(0.75, "Loading systems...")

    movement_system = MovementSystem()
    font = pygame.font.Font(Config.get_assets(key="font"), 18)
    world.add_processor(SoundSystem())
    world.add_processor(LoadingUISystem(screen, font), priority=999)
    world.add_processor(movement_system)
    world.add_processor(TerrainEffectSystem(map))
    world.add_processor(CollisionSystem(map))
    world.add_processor(AiSystem())
    selection_system = SelectionSystem(get_player_manager())
    player_movement_system = PlayerMoveSystem()
    DATA_BUS.register(DataBusKey.PLAYER_MOVEMENT_SYSTEM, player_movement_system)
    world.add_processor(player_movement_system)
    world.add_processor(EconomySystem(get_event_bus()))
    death_handler = DeathEventHandler(get_event_bus())
    targeting_system = TargetingSystem()
    world.add_processor(targeting_system)
    world.add_processor(CombatSystem())
    world.add_processor(CameraSystem(get_camera()))

    # Charger les systèmes de rendu
    update_loading(0.85, "Loading rendering systems...")

    DATA_BUS.register(DataBusKey.NOTIFICATION_MANAGER, NotificationManager())
    input_manager = InputManager()
    render = RenderSystem(screen, map, sprites)
    victory_system = VictorySystem()
    arrow_system = ArrowSystem(render)

    # Pathfinding system (doit être créé avant les systèmes de debug)
    pathfinding_system = PathfindingSystem()

    # Debug systems (après pathfinding)
    debug_render_system = DebugRenderSystem(screen, pathfinding_system)
    debug_event_handler = DebugEventHandler(pathfinding_system)

    world.add_processor(input_manager)
    world.add_processor(render)
    world.add_processor(arrow_system)  # Après le rendu de base
    world.add_processor(pathfinding_system)  # Avant les systèmes de debug
    world.add_processor(debug_event_handler)  # Écoute les événements F3
    world.add_processor(InputRouterSystem())
    world.add_processor(victory_system)

    world.add_processor(LOVAAiSystem(pathfinding_system))
    world.add_processor(SCPRAISystem())

    # Pause menu system (needs reference to game_hud for timer pause)
    pause_menu_system = PauseMenuSystem(screen, font, game_hud)
    world.add_processor(pause_menu_system)

    # Subscribe to quit to menu event
    def on_quit_to_menu(event: QuitToMenuEvent):
        game_state["running"] = False
        game_state["return_to_menu"] = True

    get_event_bus().subscribe(QuitToMenuEvent, on_quit_to_menu)

    # J'ai fait un dictionnaire pour que lorsque le quitsystem modifie la valeur, la valeur est modifiée dans ce fichier aussi
    game_state = {"running": True, "return_to_menu": False}

    world.add_processor(QuitSystem(get_event_bus(), game_state))

    # Finaliser
    update_loading(0.95, "Finalizing...")

    pygame.transform.set_smoothscale_backend("GENERIC")

    # Chargement terminé
    update_loading(1.0, "Ready ! ")
    pygame.time.wait(500)  # Pause brève pour voir "Ready!"
    get_event_bus().emit(LoadingFinishEvent(success=True))

    DATA_BUS.register(DataBusKey.PLAYED_TIME, Timer("game"))

    world_perception = WorldPerception(
        get_config().get("tile_size", 32),
        {
            EntityType.BRUTE: (get_entity(EntityType.BRUTE).get_component(Attack)).range
            * tile_size,
            EntityType.GHAST: (get_entity(EntityType.GHAST).get_component(Attack)).range
            * tile_size,
        },
    )

    DATA_BUS.register(DataBusKey.WORLD_PERCEPTION, world_perception)

    while game_state["running"]:

        clock.tick(60)

        dt = min(clock.get_time() / 1000, dt)

        for event in pygame.event.get():
            # If paused, let pause menu handle events first
            if pause_menu_system.is_paused:
                if pause_menu_system.handle_event(event):
                    continue

            # Normal game events
            victory_handled = victory_system.handle_victory_input(event)
            if not victory_handled:
                hud_handled = game_hud.process_event(event)
                if not hud_handled:
                    input_manager.handle_event(event)

        # Only process game if not paused
        if not pause_menu_system.is_paused and not victory_handled:
            world.process(dt)
            world_perception.update()

        if not victory_handled:
            render.show_map()
            render.process(dt)
            arrow_system.process(dt)
            debug_render_system.process(dt)  # Debug après le rendu principal
            selection_system.draw_selections(screen)
            game_hud.draw(dt)
            get_notification_manager().draw(screen)

            # Always draw pause menu on top
            pause_menu_system.process(dt)

        pygame.display.flip()

    # Clean up world resources
    returning_to_menu = game_state.get("return_to_menu", False)

    reset()

    # Only quit pygame if not returning to menu
    if not returning_to_menu:
        pygame.quit()

    # Return to menu if requested
    return returning_to_menu


def resize(screen: pygame.Surface, map_size: int, hud_width: int = 100) -> tuple[int]:

    global r_tile_size
    r_tile_size = (screen.get_width() - hud_width * 2) / map_size
    map_width = r_tile_size * map_size
    map_height = r_tile_size * map_size

    screen_rect = screen.get_rect()

    get_camera().set_size(screen_rect.width - (hud_width * 2) - 20, screen_rect.height)
    get_camera().set_world_size(map_width, map_height)
    get_camera().set_offset(hud_width + 10, 0)

    return map_width, map_height


def reset():
    """Reset the engine state, clearing data bus entries."""
    DATA_BUS.remove(DataBusKey.PLAYED_TIME)
    DATA_BUS.remove(DataBusKey.MAP)
    DATA_BUS.remove(DataBusKey.PLAYER_MANAGER)
    DATA_BUS.remove(DataBusKey.NOTIFICATION_MANAGER)
    DATA_BUS.remove(DataBusKey.PLAYER_MOVEMENT_SYSTEM)
    DATA_BUS.remove(DataBusKey.WORLD_PERCEPTION)

    esper.clear_database()
    esper.clear_cache()
    esper.clear_dead_entities()
    esper._processors = []

    get_event_bus()._subscribers.clear()
