import pygame
from events.sound_event import SoundEvent
from enums.sounds import sounds


class SoundEventHandler:
    """Handles the use of sound effects (SFX)."""

    def __init__(self, event_bus, volume: int = 100):
        self.event_bus = event_bus
        self.volume = volume
        self.event_bus.subscribe(SoundEvent, self.handle_sound)

    def set_volume(self, volume: int):
        self.volume = volume

    def handle_sound(self, sound_event: SoundEvent):
        """
        Play the sound corresponding to the event.

        Args:
            sound_event: Event with the sound's info
        """

        if sounds[sound_event.origin][sound_event.model][sound_event.reason]:
            sound_to_play = pygame.mixer.Sound(
                sounds[sound_event.origin][sound_event.model][sound_event.reason]
            )
            sound_to_play.set_volume(self.volume)
            sound_to_play.play()
