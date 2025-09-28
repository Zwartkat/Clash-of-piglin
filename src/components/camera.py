from components.position import Position


class Camera:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.x = 0
        self.y = 0
        self.zoom_factor = 1.0

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def zoom(self, dz: float):
        self.zoom_factor += dz
        if self.zoom_factor < 0.8:
            self.zoom_factor = 0.8

    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height

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
