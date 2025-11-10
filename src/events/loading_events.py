"""Events for map/game loading progress."""


class LoadingStartEvent:
    """Emitted when loading starts."""

    def __init__(self, message: str = "Loading..."):
        self.message = message


class LoadingProgressEvent:
    """Emitted during loading to update progress."""

    def __init__(self, progress: float, message: str = ""):
        self.progress = max(0.0, min(1.0, progress))  # clamp 0-1
        self.message = message


class LoadingFinishEvent:
    """Emitted when loading completes."""

    def __init__(self, success: bool = True):
        self.success = success
