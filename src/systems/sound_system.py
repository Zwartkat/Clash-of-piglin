import esper
import pygame
from core.accessors import get_event_bus
from events.arrow_fired_event import ArrowFiredEvent

pygame.mixer.init()

class SoundSystem(esper.Processor):

    MUSIC_VOLUME = 1.0
    SOUNDS_VOLUME = 1.0

    # Chargement de tous les sons pour ne pas les recréer à chaque fois qu'on veut les jouer
    SOUNDS = {
        "arrow_fired": pygame.mixer.Sound("assets/audio/sounds/arrow_fired.mp3")
    }

    def __init__(self):
        super().__init__()

        get_event_bus().subscribe(ArrowFiredEvent, self.play_arrow_fired)

    
    def process(self, dt):
        pass
        
    @staticmethod
    def update_volume():
        """
        Méthode pour mettre à jour le volume du jeu
        """

        # Mise à jour du volume de la musique
        pygame.mixer.music.set_volume(SoundSystem.MUSIC_VOLUME)

        # Mise à jour du volume de tous les sons
        for sound in SoundSystem.SOUNDS.values():
            sound.set_volume(SoundSystem.SOUNDS_VOLUME)

    def play_arrow_fired(self, event: ArrowFiredEvent):
        SoundSystem.SOUNDS["arrow_fired"].play()