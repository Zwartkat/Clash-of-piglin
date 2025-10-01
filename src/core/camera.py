from components.position import Position


class Camera:
    def __init__(self):
        self.width: int = 0
        self.height: int = 0
        self.x: int = 0
        self.y: int = 0
        self.zoom_factor: float = 1.0
        self.world_width: int = 100
        self.world_height: int = 100

    def move(self, dx: int, dy: int) -> None:
        """
        Move the camera by a given offset while keeping it inside world bounds.

        Args:
            dx (int): Offset in the x direction (world units).
            dy (int): Offset in the y direction (world units).
        """
        self.x += dx
        self.y += dy

        max_x = max(0, self.world_width - self.width / self.zoom_factor)
        max_y = max(0, self.world_height - self.height / self.zoom_factor)

        self.x = min(max(self.x, 0), max_x)
        self.y = min(max(self.y, 0), max_y)

    def zoom(self, dz: float) -> None:
        """
        Adjust the zoom level with limits.

        Args:
            dz (float): Change in zoom factor (positive = zoom in, negative = zoom out).
        """
        self.min_zoom = 0.5
        self.max_zoom = 50.0
        self.zoom_factor += dz
        min_zoom_x = (
            self.width / self.world_width if self.world_width else self.min_zoom
        )
        min_zoom_y = (
            self.height / self.world_height if self.world_height else self.min_zoom
        )
        dynamic_min_zoom = max(min_zoom_x, min_zoom_y, self.min_zoom)

        self.zoom_factor = max(dynamic_min_zoom, min(self.zoom_factor, self.max_zoom))
        self.x = min(self.x, max(0, self.world_width - self.width / self.zoom_factor))
        self.y = min(self.y, max(0, self.world_height - self.height / self.zoom_factor))

    def set_size(self, width: int, height: int) -> None:
        """
        Set the viewport (screen) size.

        Args:
            width (int): Width in pixels.
            height (int): Height in pixels.
        """
        self.width = width
        self.height = height

    def set_world_size(self, width: int, height: int) -> None:
        """
        Set the world (map) size.

        Args:
            width (int): World width in units.
            height (int): World height in units.
        """
        self.world_width = width
        self.world_height = height

    def set_position(self, x: int, y: int) -> None:
        """
        Set the camera position directly.

        Args:
            x (int): X position in world coordinates.
            y (int): Y position in world coordinates.
        """
        self.x = x
        self.y = y

    def set_zoom(self, zoom: float) -> None:
        """
        Set the zoom level directly.

        Args:
            zoom (float): Zoom factor.
        """

        self.zoom_factor = zoom

    def apply(self, x: int, y: int) -> tuple[int]:
        """
        Convert world coordinates to screen coordinates.

        Args:
            x (int): World x coordinate.
            y (int): World y coordinate.

        Returns:
            tuple[float, float]: Transformed (x, y) screen coordinates.
        """
        return (x - self.x) * self.zoom_factor, (y - self.y) * self.zoom_factor

    def apply_position(self, position: Position) -> Position:
        """
        Convert a Position component from world to screen coordinates.

        Args:
            position (Position): Position in world coordinates.

        Returns:
            Position: Transformed position in screen coordinates.
        """
        x, y = self.apply(position.x, position.y)
        return Position(x, y)

    def unapply(self, x: int, y: int) -> tuple[int]:
        """
        Convert screen coordinates back to world coordinates.

        Args:
            x (int): Screen x coordinate.
            y (int): Screen y coordinate.

        Returns:
            tuple[float, float]: Transformed (x, y) world coordinates.
        """
        return x / self.zoom_factor + self.x, y / self.zoom_factor + self.y


CAMERA = Camera()
