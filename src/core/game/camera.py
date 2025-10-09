from components.base.position import Position


class Camera:
    def __init__(self):
        self.width: int = 0
        self.height: int = 0
        self.x: int = 0
        self.y: int = 0
        self.zoom_factor: float = 1.0
        self.world_width: int = 100
        self.world_height: int = 100
        self.offset_x: int = 0
        self.offset_y: int = 0

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

        self.zoom_factor = max(dynamic_min_zoom, min(self.zoom_factor, self.max_zoom))
        self.x = min(self.x, max(0, self.world_width - self.width / self.zoom_factor))
        self.y = min(self.y, max(0, self.world_height - self.height / self.zoom_factor))

    def set_offset(self, offset_x: int, offset_y: int):
        """
        Set the offset of the camera

        Args:
            offset_x (int): X offset
            offset_y (int): Y offset
        """
        self.offset_x = offset_x
        self.offset_y = offset_y

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
        return (x - self.x) * self.zoom_factor + self.offset_x, (
            y - self.y
        ) * self.zoom_factor + self.offset_y

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
        return (x - self.offset_x) / self.zoom_factor + self.x, (
            y - self.offset_y
        ) / self.zoom_factor + self.y

    def is_visible(self, x: float, y: float, w: float = 0, h: float = 0) -> bool:
        """
        Vérifie si un objet (x, y, w, h) est visible dans la caméra.
        Coordonnées en unités du monde.
        """
        cam_x1, cam_y1 = self.x, self.y
        cam_x2 = self.x + (self.width) / self.zoom_factor
        cam_y2 = self.y + (self.height) / self.zoom_factor

        obj_x1, obj_y1 = x, y
        obj_x2, obj_y2 = x + w, y + h

        return not (
            obj_x2 < cam_x1 or obj_x1 > cam_x2 or obj_y2 < cam_y1 or obj_y1 > cam_y2
        )


CAMERA = Camera()
