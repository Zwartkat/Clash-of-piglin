from components.position import Position


class Camera:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.x = 0
        self.y = 0
        self.zoom_factor = 1.0
        self.world_width = 100
        self.world_height = 100

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

        max_x = max(0, self.world_width - self.width / self.zoom_factor)
        max_y = max(0, self.world_height - self.height / self.zoom_factor)

        self.x = min(max(self.x, 0), max_x)
        self.y = min(max(self.y, 0), max_y)

    def zoom(self, dz: float):
        self.min_zoom = 1.0
        self.max_zoom = 5.0
        self.zoom_factor += dz
        min_zoom_x = (
            self.width / self.world_width if self.world_width else self.min_zoom
        )
        min_zoom_y = (
            self.height / self.world_height if self.world_height else self.min_zoom
        )
        dynamic_min_zoom = max(min_zoom_x, min_zoom_y, self.min_zoom)

        # Appliquer les bornes
        self.zoom_factor = max(dynamic_min_zoom, min(self.zoom_factor, self.max_zoom))

        # Re-clamp position après zoom
        self.x = min(self.x, max(0, self.world_width - self.width / self.zoom_factor))
        self.y = min(self.y, max(0, self.world_height - self.height / self.zoom_factor))

    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def set_world_size(self, width: int, height: int):
        self.world_width = width
        self.world_height = height

    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y

    def set_zoom(self, zoom: float):
        self.zoom_factor = zoom

    def apply(self, x: int, y: int):
        return (x - self.x) * self.zoom_factor, (y - self.y) * self.zoom_factor

    def apply_position(self, position: Position):
        x, y = self.apply(position.x, position.y)
        return Position(x, y)

    def unapply(self, x: int, y: int):
        return x / self.zoom_factor + self.x, y / self.zoom_factor + self.y


CAMERA = Camera()
