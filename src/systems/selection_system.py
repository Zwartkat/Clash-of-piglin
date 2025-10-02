import pygame
import esper
from core.camera import CAMERA
from components.health import Health
from components.position import Position
from components.selection import Selection
from components.team import PLAYER_1_TEAM, PLAYER_2_TEAM, Team
from components.collider import Collider
from enums.unit_type import UnitType


class SelectionSystem:
    """Handles unit selection with mouse clicks and drag rectangles."""

    def __init__(self, player_manager):
        self.player_manager = player_manager
        self.is_dragging = False
        self.selection_start = None
        self.selection_rect = None
        self.drag_threshold = 5  # Minimum pixels to consider it a drag

    def handle_mouse_down(self, mouse_pos, world):
        """
        Start selection process when mouse button is pressed.

        Args:
            mouse_pos: Mouse click position (x, y) on screen
            world: Game world (not used but kept for consistency)
        """
        self.selection_start = mouse_pos
        self.is_dragging = False

    def handle_mouse_motion(self, mouse_pos, world):
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

                start_x, start_y = self.selection_start
                end_x, end_y = mouse_pos

                left = min(start_x, end_x)
                top = min(start_y, end_y)
                width = abs(end_x - start_x)
                height = abs(end_y - start_y)

                left, top = CAMERA.apply(left, top)

                self.selection_rect = pygame.Rect(left, top, width, height)

    def handle_mouse_up(self, mouse_pos, world):
        """
        Complete selection when mouse button is released.

        Args:
            mouse_pos: Mouse release position (x, y) on screen
            world: Game world to search for entities
        """
        if self.is_dragging:
            self.select_entities_in_rect(world)
        else:
            self.select_entity_at_point(mouse_pos, world)

        self.selection_start = None
        self.selection_rect = None
        self.is_dragging = False

    def select_entity_at_point(self, mouse_pos, world):
        """
        Select single entity at mouse click position.

        Args:
            mouse_pos: Mouse click position (x, y) on screen
            world: Game world to search for entities
        """
        self.clear_selection(world)
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

    def select_entities_in_rect(self, world):
        """
        Select all entities inside the drag rectangle.

        Args:
            world: Game world to search for entities
        """
        if not self.selection_rect:
            return

        self.clear_selection(world)

        for ent, (pos, team) in esper.get_components(Position, Team):
            # Only select units from current player's team
            if team.team_id == self.player_manager.get_current_player():
                pos = CAMERA.apply_position(pos)
                if self.selection_rect.collidepoint(pos.x, pos.y):
                    if esper.has_component(ent, Selection):
                        selection = esper.component_for_entity(ent, Selection)
                        selection.is_selected = True
                    else:
                        esper.add_component(ent, Selection(True))

    def clear_selection(self, world):
        """
        Remove selection from all entities.

        Args:
            world: Game world (not used but kept for consistency)
        """
        for ent, selection in esper.get_component(Selection):
            selection.is_selected = False

    def get_selected_entities(self, world):
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

    def draw_selections(self, screen, world):
        """
        Draw selection indicators and team colors around all entities.

        Args:
            screen: Pygame screen surface to draw on
            world: Game world (not used but kept for consistency)
        """
        current_team = self.player_manager.get_current_player()

        for ent, pos in esper.get_component(Position):
            if not esper.has_component(ent, Team):
                continue

            team = esper.component_for_entity(ent, Team)
            if team.team_id not in [PLAYER_1_TEAM, PLAYER_2_TEAM]:
                continue

            if not esper.has_component(ent, Collider):
                continue

            collider = esper.component_for_entity(ent, Collider)

            left = int(pos.x - collider.width // 2)
            top = int(pos.y - collider.height // 2)

            # Set team colors: green for player 1, red for player 2
            if team.team_id == PLAYER_1_TEAM:
                team_outline = (0, 255, 0)
            else:
                team_outline = (255, 0, 0)

            entity_rect = pygame.Rect(left, top, collider.width, collider.height)

            # Draw team outline (thicker for current player)
            if team.team_id == current_team:
                pygame.draw.rect(screen, team_outline, entity_rect, 2)
            else:
                pygame.draw.rect(screen, team_outline, entity_rect, 1)

            # Draw selection highlight for selected units
            if team.team_id == current_team and esper.has_component(ent, Selection):
                selection = esper.component_for_entity(ent, Selection)
                if selection.is_selected:
                    selection_rect = pygame.Rect(
                        left - 3, top - 3, collider.width + 6, collider.height + 6
                    )
                    # Uncomment to draw orange selection border
                    # pygame.draw.rect(screen, (255, 165, 0), selection_rect, 3)

        self.draw_selection_rect(screen)
