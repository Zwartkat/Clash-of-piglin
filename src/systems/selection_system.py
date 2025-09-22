import pygame
import esper
from components.position import Position
from components.selection import Selection
from components.team import PLAYER_TEAM, Team
from components.collider import Collider
from config.unit_stats import UNIT_COLORS
from components.stats import UnitType


class SelectionSystem:
    def __init__(self):
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
            if team.team_id == PLAYER_TEAM:
                dx = mouse_pos[0] - pos.x
                dy = mouse_pos[1] - pos.y
                distance = (dx**2 + dy**2) ** 0.5

                if esper.has_component(ent, Collider):
                    collider = esper.component_for_entity(ent, Collider)
                    rect_x = pos.x - collider.width / 2
                    rect_y = pos.y - collider.height / 2
                    rect = pygame.Rect(rect_x, rect_y, collider.width, collider.height)

                    if rect.collidepoint(mouse_pos) and distance < closest_distance:
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
            if team.team_id == PLAYER_TEAM:
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
        for ent, pos in esper.get_component(Position):
            if not esper.has_component(ent, Team):
                continue

            team = esper.component_for_entity(ent, Team)
            if team.team_id != PLAYER_TEAM:
                continue

            if esper.has_component(ent, UnitType):
                unit_type_comp = esper.component_for_entity(ent, UnitType)
                color = UNIT_COLORS.get(unit_type_comp.unit_type, (255, 255, 255))
                pygame.draw.circle(screen, color, (int(pos.x), int(pos.y)), 12)
            else:
                if esper.has_component(ent, Collider):
                    collider = esper.component_for_entity(ent, Collider)
                    rect_x = int(pos.x - collider.width / 2)
                    rect_y = int(pos.y - collider.height / 2)
                    rect = pygame.Rect(rect_x, rect_y, collider.width, collider.height)
                    pygame.draw.rect(screen, (255, 0, 0), rect)
                else:
                    pygame.draw.rect(
                        screen, (255, 0, 0), (int(pos.x - 5), int(pos.y - 5), 10, 10)
                    )

            if esper.has_component(ent, Selection):
                selection = esper.component_for_entity(ent, Selection)
                if selection.is_selected:
                    self.draw_diamond(screen, pos, (255, 165, 0))
                else:
                    self.draw_diamond(screen, pos, (0, 100, 255))
            else:
                self.draw_diamond(screen, pos, (0, 100, 255))

        self.draw_selection_rect(screen)

    def draw_diamond(self, screen, pos, color):
        diamond_points = [
            (int(pos.x), int(pos.y - 15)),  # Top
            (int(pos.x + 8), int(pos.y - 7)),  # right
            (int(pos.x), int(pos.y + 1)),  # bottom
            (int(pos.x - 8), int(pos.y - 7)),  # left
        ]

        pygame.draw.polygon(screen, color, diamond_points)
        pygame.draw.polygon(screen, (0, 0, 0), diamond_points, 1)
