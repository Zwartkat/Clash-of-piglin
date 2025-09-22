from core.iterator_system import IteratingProcessor
from components.position import Position
from components.collider import Collider
import esper


class CollisionSystem(IteratingProcessor):
    def __init__(self, game_map):
        super().__init__(Position, Collider)
        self.game_map = game_map

    def process_entity(self, ent1, dt, pos1, collider1):
        for ent2, (pos2, collider2) in esper.get_components(Position, Collider):
            if ent1 != ent2 and self.check_collision(pos1, collider1, pos2, collider2):
                self.resolve_collision(pos1, pos2, collider1, collider2)

    def check_collision(self, pos1, col1, pos2, col2):
        dx = abs(pos2.x - pos1.x)
        dy = abs(pos2.y - pos1.y)
        half_width = (col1.width + col2.width) / 2
        half_height = (col1.height + col2.height) / 2
        return dx < half_width and dy < half_height

    def resolve_collision(self, pos1, pos2, col1, col2):
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance < 0.1:
            dx, dy = 1, 0
            distance = 1

        dx /= distance
        dy /= distance

        min_distance = (col1.width + col2.width) / 2
        push_distance = (min_distance - distance) / 2

        pos1.x += dx * push_distance
        pos1.y += dy * push_distance
        pos2.x -= dx * push_distance
        pos2.y -= dy * push_distance
