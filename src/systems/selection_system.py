import pygame
import esper
from components.camera import CAMERA
from components.health import Health
from components.position import Position
from components.selection import Selection
from components.team import PLAYER_1_TEAM, PLAYER_2_TEAM, Team
from components.collider import Collider
from components.stats import UnitType


class SelectionSystem:
    def __init__(self, player_manager):
        self.player_manager = player_manager
        self.is_dragging = False
        self.selection_start = None
        self.selection_rect = None
        self.drag_threshold = 5  # Minimum pixels to consider it a drag

    def handle_mouse_down(self, mouse_pos, world):
        self.selection_start = mouse_pos
        self.is_dragging = False

    def handle_mouse_motion(self, mouse_pos, world):
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
        if self.is_dragging:
            self.select_entities_in_rect(world)
        else:
            self.select_entity_at_point(mouse_pos, world)

        self.selection_start = None
        self.selection_rect = None
        self.is_dragging = False

    def select_entity_at_point(self, mouse_pos, world):
        self.clear_selection(world)
        closest_entity = None
        closest_distance = float("inf")

        for ent, (pos, team) in esper.get_components(Position, Team):
            # pos = CAMERA.apply_position(pos)
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

        if closest_entity:
            if esper.has_component(closest_entity, Selection):
                selection = esper.component_for_entity(closest_entity, Selection)
                selection.is_selected = True
            else:
                esper.add_component(closest_entity, Selection(True))

    def select_entities_in_rect(self, world):
        if not self.selection_rect:
            return

        self.clear_selection(world)

        for ent, (pos, team) in esper.get_components(Position, Team):

            print(team.team_id, self.player_manager.get_current_player())
            if team.team_id == self.player_manager.get_current_player():
                pos = CAMERA.apply_position(pos)
                if self.selection_rect.collidepoint(pos.x, pos.y):
                    if esper.has_component(ent, Selection):
                        selection = esper.component_for_entity(ent, Selection)
                        selection.is_selected = True
                    else:
                        esper.add_component(ent, Selection(True))

    def clear_selection(self, world):
        for ent, selection in esper.get_component(Selection):
            selection.is_selected = False

    def get_selected_entities(self, world):
        selected = []
        for ent, selection in esper.get_component(Selection):
            if selection.is_selected:
                selected.append(ent)
        return selected

    def draw_selection_rect(self, screen):
        if self.is_dragging and self.selection_rect:
            pygame.draw.rect(screen, (255, 255, 255), self.selection_rect, 2)
            overlay = pygame.Surface(
                (self.selection_rect.width, self.selection_rect.height)
            )
            overlay.set_alpha(30)
            overlay.fill((255, 255, 255))
            screen.blit(overlay, (self.selection_rect.x, self.selection_rect.y))

    def draw_selections(self, screen, world):
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

            base_color = (255, 255, 255)
            if esper.has_component(ent, UnitType):
                unit_type_comp = esper.component_for_entity(ent, UnitType)
                # base_color = UNIT_COLORS.get(unit_type_comp.unit_type, (255, 255, 255))

            if team.team_id == PLAYER_1_TEAM:
                # color = base_color
                team_outline = (0, 255, 0)
            else:
                color = tuple(c // 2 for c in base_color)
                team_outline = (255, 0, 0)

            entity_rect = pygame.Rect(left, top, collider.width, collider.height)
            # pygame.draw.rect(screen, color, entity_rect)

            if team.team_id == current_team:
                pygame.draw.rect(screen, team_outline, entity_rect, 2)
            else:
                pygame.draw.rect(screen, team_outline, entity_rect, 1)

            # if esper.has_component(ent, Health):
            #    health = esper.component_for_entity(ent, Health)
            #    if health.remaining < health.full:
            #        self._draw_health_bar(screen, pos, collider, health)

            if team.team_id == current_team and esper.has_component(ent, Selection):
                selection = esper.component_for_entity(ent, Selection)
                if selection.is_selected:
                    selection_rect = pygame.Rect(
                        left - 3, top - 3, collider.width + 6, collider.height + 6
                    )
                    # pygame.draw.rect(screen, (255, 165, 0), selection_rect, 3)

        self.draw_selection_rect(screen)

    def draw_diamond(self, screen, pos, color):
        diamond_points = [
            (int(pos.x), int(pos.y - 5)),  # Top
            (int(pos.x + 2), int(pos.y - 3)),  # right
            (int(pos.x), int(pos.y + 1)),  # bottom
            (int(pos.x - 2), int(pos.y - 3)),  # left
        ]

        pygame.draw.polygon(screen, color, diamond_points)
        pygame.draw.polygon(screen, (0, 0, 0), diamond_points, 1)

    def _draw_health_bar(self, screen, pos, collider, health):
        bar_width = collider.width
        bar_height = 4

        bar_x = int(pos.x - bar_width // 2)
        bar_y = int(pos.y - collider.height // 2 - bar_height - 3)

        # black background
        pygame.draw.rect(
            screen, (0, 0, 0), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2)
        )

        # Red background (HP lost)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # Green bar (HP remaining)
        hp_ratio = max(0, health.remaining / health.full)  # between 0 and 1
        green_width = int(bar_width * hp_ratio)
        if green_width > 0:
            pygame.draw.rect(
                screen, (0, 255, 0), (bar_x, bar_y, green_width, bar_height)
            )
