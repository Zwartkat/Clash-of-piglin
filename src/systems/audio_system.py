from core.accessors import get_event_bus
from enums.sounds import origin, reasons, sounds
from events.sound_event import SoundEvent


class AudioSystem:

    def __init__(self):
        return

    def play_sound(self, origin, type, reason):
        if (
            origin in sounds
            and type in sounds[origin]
            and reason in sounds[origin][type]
        ):
            get_event_bus().emit(SoundEvent(origin, type, reason))

    def play_music(self): ...
