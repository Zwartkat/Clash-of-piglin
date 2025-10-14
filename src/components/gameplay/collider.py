from core.ecs.component import Component


class Collider(Component):
    def __init__(self, width, height, collision_type="unit"):
        self.width = width
        self.height = height

    def get_bounds(self, position):
        return (position.x, position.y, self.width, self.height)
