import pygame
import esper
from components.base.velocity import Velocity
from core.accessors import get_event_bus, get_player_manager
from core.game.camera import CAMERA
from components.base.health import Health
from components.base.position import Position
from components.gameplay.selection import Selection
from components.base.team import PLAYER_1_TEAM, PLAYER_2_TEAM, Team
from components.gameplay.collider import Collider
from enums.entity.unit_type import UnitType
from events.switch_event import SwitchEvent
from events.start_select_event import StartSelectEvent
from events.stop_select_event import StopSelectEvent
from events.select_event import SelectEvent
from events.move_order_event import MoveOrderEvent
from events.event_move import EventMoveTo
from core.ecs.event_bus import EventBus


class SelectionSystem:
    """Handles unit selection with mouse clicks and drag rectangles."""

    def __init__(self, player_manager):
        self.player_manager = player_manager
        self.is_dragging = False
        self.selection_start = None
        self.selection_rect = None
        self.drag_threshold = 5  # Minimum pixels to consider it a drag
        get_event_bus().subscribe(SwitchEvent, self.on_switch)
        get_event_bus().subscribe(
            StartSelectEvent, lambda e: self.handle_mouse_down(e.pos)
        )
        get_event_bus().subscribe(
            StopSelectEvent, lambda e: self.handle_mouse_up(e.pos)
        )
        get_event_bus().subscribe(
            SelectEvent, lambda e: self.handle_mouse_motion(e.pos)
        )
        get_event_bus().subscribe(MoveOrderEvent, self.on_move_order)

    def handle_mouse_down(self, mouse_pos):
        """
        Start selection process when mouse button is pressed.

        Args:
            mouse_pos: Mouse click position (x, y) on screen
            world: Game world (not used but kept for consistency)
        """
        self.selection_start = mouse_pos
        self.is_dragging = False

    def handle_mouse_motion(self, mouse_pos):
        """
        Update selection rectangle while mouse is being dragged.

        Args:
            mouse_pos: Current mouse position (x, y) on screen
            world: Game world (not used but kept for consistency)
        """
        if self.selection_start:
            dx = mouse_pos[0] - self.selection_start[0]
            dy = mouse_pos[1] - self.selection_start[1]

            distance = (dx**2 + dy**2) ** 0.5

            if distance > self.drag_threshold:
                self.is_dragging = True

                start_x, start_y = CAMERA.apply(
                    self.selection_start[0], self.selection_start[1]
                )
                end_x, end_y = CAMERA.apply(mouse_pos[0], mouse_pos[1])

                left = min(start_x, end_x)
                top = min(start_y, end_y)
                width = abs(end_x - start_x)
                height = abs(end_y - start_y)

                self.selection_rect = pygame.Rect(left, top, width, height)

    def handle_mouse_up(self, mouse_pos):
        """
        Complete selection when mouse button is released.

        Args:
            mouse_pos: Mouse release position (x, y) on screen
            world: Game world to search for entities
        """
        if self.is_dragging:
            self.select_entities_in_rect()
        else:
            self.select_entity_at_point(mouse_pos)

        self.selection_start = None
        self.selection_rect = None
        self.is_dragging = False

    def select_entity_at_point(self, mouse_pos):
        """
        Select single entity at mouse click position.

        Args:
            mouse_pos: Mouse click position (x, y) on screen
            world: Game world to search for entities
        """
        self.clear_selection()
        closest_entity = None
        closest_distance = float("inf")

        for ent, (pos, team) in esper.get_components(Position, Team):
            # Only select units from current player's team
            if team.team_id == self.player_manager.get_current_player():
                dx = mouse_pos[0] - pos.x
                dy = mouse_pos[1] - pos.y
                distance = (dx**2 + dy**2) ** 0.5

                if esper.has_component(ent, Collider):
                    collider = esper.component_for_entity(ent, Collider)
                    left = pos.x - collider.width // 2
                    top = pos.y - collider.height // 2
                    entity_rect = pygame.Rect(
                        left, top, collider.width, collider.height
                    )

                    if (
                        entity_rect.collidepoint(mouse_pos)
                        and distance < closest_distance
                    ):
                        closest_entity = ent
                        closest_distance = distance

        # Mark closest entity as selected
        if closest_entity:
            if esper.has_component(closest_entity, Selection):
                selection = esper.component_for_entity(closest_entity, Selection)
                selection.is_selected = True
            else:
                esper.add_component(closest_entity, Selection(True))

    def select_entities_in_rect(self):
        """
        Select all entities inside the drag rectangle.

        Args:
            world: Game world to search for entities
        """
        if not self.selection_rect:
            return

        self.clear_selection()

        for ent, (pos, team, velocity) in esper.get_components(
            Position, Team, Velocity
        ):
            # Only select units from current player's team
            if team.team_id == self.player_manager.get_current_player():
                pos = CAMERA.apply_position(pos)
                if self.selection_rect.collidepoint(pos.x, pos.y):
                    if esper.has_component(ent, Selection):
                        selection = esper.component_for_entity(ent, Selection)
                        selection.is_selected = True
                    else:
                        esper.add_component(ent, Selection(True))

    def clear_selection(self):
        """
        Remove selection from all entities.

        Args:
            world: Game world (not used but kept for consistency)
        """
        for ent, selection in esper.get_component(Selection):
            selection.is_selected = False

    def get_selected_entities(self):
        """
        Get list of all currently selected entities.

        Args:
            world: Game world (not used but kept for consistency)

        Returns:
            list: Entity IDs that are currently selected
        """
        selected = []
        for ent, selection in esper.get_component(Selection):
            if selection.is_selected:
                selected.append(ent)
        return selected

    def draw_selection_rect(self, screen):
        """
        Draw the drag selection rectangle on screen.

        Args:
            screen: Pygame screen surface to draw on
        """
        if self.is_dragging and self.selection_rect:
            pygame.draw.rect(screen, (255, 255, 255), self.selection_rect, 2)
            overlay = pygame.Surface(
                (self.selection_rect.width, self.selection_rect.height)
            )
            overlay.set_alpha(30)
            overlay.fill((255, 255, 255))
            screen.blit(overlay, (self.selection_rect.x, self.selection_rect.y))

    def draw_selections(self, screen):
        """
        Draw selection indicators and team colors around all entities.

        Args:
            screen: Pygame screen surface to draw on
            world: Game world (not used but kept for consistency)
        """

        for ent, pos in esper.get_component(Position):
            if not esper.has_component(ent, Team):
                continue

            team = esper.component_for_entity(ent, Team)
            if team.team_id not in [PLAYER_1_TEAM, PLAYER_2_TEAM]:
                continue

            if not esper.has_component(ent, Collider):
                continue

        self.draw_selection_rect(screen)

    def on_switch(self, event: SwitchEvent):
        get_player_manager().switch_player()
        self.clear_selection()

    def on_move_order(self, event: MoveOrderEvent):
        selected_entities = self.get_selected_entities()

        if selected_entities:
            x, y = event.pos
            from systems.combat.troop_system import (
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
                    get_event_bus().emit(EventMoveTo(ent, target_x, target_y))
