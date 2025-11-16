"""Pause menu events."""


class PauseToggleEvent:
    """Event emitted when ESC is pressed to toggle pause."""

    pass


class ResumeGameEvent:
    """Event emitted when player resumes the game."""

    pass


class QuitToMenuEvent:
    """Event emitted when player wants to quit to main menu."""

    pass
