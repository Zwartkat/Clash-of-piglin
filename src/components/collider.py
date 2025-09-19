class Collider:
    def __init__(self, width, height, collision_type="unit"):
        self.width = width
        self.height = height
        self.collision_type = collision_type  # "unit", "wall", "projectile", etc.

    def get_bounds(self, position):
        return (position.x, position.y, self.width, self.height)
