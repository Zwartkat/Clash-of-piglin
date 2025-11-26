import pygame
import esper
from ui.hud import Hud
from enums.entity.entity_type import EntityType
from enums.input_actions import InputAction


class HudManager:
    """Système gérant l'interface utilisateur du jeu"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.hud = Hud(screen)
        self._input_manager = None

    def _get_input_manager(self):
        """Get InputManager from esper processors."""
        if self._input_manager is None:
            from core.input.input_manager import InputManager

            for processor in esper._processors:
                if isinstance(processor, InputManager):
                    self._input_manager = processor
                    break
        return self._input_manager

    def draw(self, dt=0.016):
        """Draw the interface with delta time for animations"""
        self.hud.draw(dt)

    def process_event(self, event):
        """Traite les événements liés à l'interface"""
        if event.type == pygame.MOUSEMOTION:
            self.hud.handle_mouse_motion(event.pos)
            return False  # Laisser passer les mouvements de souris
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Vérifier si le clic est sur l'interface
            if self.hud.is_click_on_hud(event.pos):
                return self.hud.handle_mouse_click(event.pos)
            return False  # Laisser passer les clics sur la map
        elif event.type == pygame.KEYDOWN:
            # Gestion des raccourcis clavier pour l'achat d'unités via InputManager
            input_mgr = self._get_input_manager()
            if input_mgr and event.key in input_mgr.key_bindings_press:
                action = input_mgr.key_bindings_press[event.key]

                # Map InputAction to unit spawn
                spawn_map = {
                    InputAction.SPAWN_T1_CROSSBOWMAN: (EntityType.CROSSBOWMAN, 1),
                    InputAction.SPAWN_T1_BRUTE: (EntityType.BRUTE, 1),
                    InputAction.SPAWN_T1_GHAST: (EntityType.GHAST, 1),
                    InputAction.SPAWN_T2_CROSSBOWMAN: (EntityType.CROSSBOWMAN, 2),
                    InputAction.SPAWN_T2_BRUTE: (EntityType.BRUTE, 2),
                    InputAction.SPAWN_T2_GHAST: (EntityType.GHAST, 2),
                }

                if action in spawn_map:
                    unit_type, team_id = spawn_map[action]
                    return self.hud.buy_unit_by_key(unit_type, team_id)

            return False
        if event.type == pygame.VIDEORESIZE:
            # Recréer le HUD avec les nouvelles dimensions
            self.hud = Hud(self.screen)
            return False
        return False
