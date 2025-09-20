import math
from core.iterator_system import IteratingProcessor
from components.position import Position
from components.team import Team

TROOP_CIRCLE = "circle"
TROOP_GRID = "grid"


class FormationSystem(IteratingProcessor):
    @staticmethod
    def calculate_formation_positions(
        entities, target_x, target_y, spacing=30, formation_type=TROOP_GRID
    ):
        """Calculate positions for entities based on formation type."""
        num_entities = len(entities)

        if num_entities == 0:
            return []
        elif num_entities == 1:
            return [(target_x, target_y)]

        positions = []

        if formation_type == TROOP_GRID:
            grid_size = int(math.ceil(math.sqrt(num_entities)))

            for i in range(num_entities):
                row = i // grid_size
                col = i % grid_size

                offset_x = (col - (grid_size - 1) / 2) * spacing
                offset_y = (row - (grid_size - 1) / 2) * spacing

                positions.append((target_x + offset_x, target_y + offset_y))

        elif formation_type == TROOP_CIRCLE:
            radius = max(spacing, num_entities * 8)
            for i in range(num_entities):
                angle = (i / num_entities) * 2 * math.pi
                pos_x = target_x + radius * math.cos(angle)
                pos_y = target_y + radius * math.sin(angle)
                positions.append((pos_x, pos_y))

        return positions
