import esper
import pygame
from core.accessors import get_debugger, get_event_bus
from events.arrow_fired_event import ArrowFiredEvent
from events.fireball_fired_event import FireballFiredEvent
from events.death_event import DeathEvent
from enums.entity.entity_type import EntityType
from events.victory_event import VictoryEvent
from events.pause_events import PauseToggleEvent, ResumeGameEvent
from events.button_clicked_event import ButtonClickedEvent

pygame.mixer.init()


class SoundSystem(esper.Processor):
    """
    System to manage sounds and musics according to events received
    """

    # Variables de classe

    # Chargement de tous les sons pour ne pas les recréer à chaque fois qu'on veut les jouer
    SOUNDS = {
        "arrow_fired": pygame.mixer.Sound("assets/audio/sounds/arrow_fired.ogg"),
        "fireball_fired": pygame.mixer.Sound("assets/audio/sounds/fireball_fired.ogg"),
        "piglin_death": pygame.mixer.Sound("assets/audio/sounds/piglin_death.ogg"),
        "ghast_death": pygame.mixer.Sound("assets/audio/sounds/ghast_death.ogg"),
        "victory": pygame.mixer.Sound("assets/audio/sounds/victory.mp3"),
        "button_clicked": pygame.mixer.Sound("assets/audio/sounds/button_clicked.ogg"),
    }

    # Répertoire des musiques (on pourra en ajouter pour le menu par exemple)
    MUSICS = {"pigstep": "assets/audio/pigstep.mp3"}

    IS_MUSIC_LOADED = False
    IS_MUSIC_PLAYED = False

    def __init__(self):
        """
        Matching every event to their sound method
        """

        super().__init__()

        get_event_bus().subscribe(ArrowFiredEvent, self.play_arrow_fired)
        get_event_bus().subscribe(FireballFiredEvent, self.play_fireball_fired)
        get_event_bus().subscribe(DeathEvent, self.play_death_sound)
        get_event_bus().subscribe(VictoryEvent, self.play_victory)
        get_event_bus().subscribe(ButtonClickedEvent, SoundSystem.play_button_clicked)
        get_event_bus().subscribe(PauseToggleEvent, SoundSystem.pause_music)
        get_event_bus().subscribe(ResumeGameEvent, SoundSystem.play_music)

    def process(self, dt):
        pass

    @staticmethod
    def set_music(music):
        pygame.mixer.music.load(music)
        SoundSystem.IS_MUSIC_LOADED = True

    @staticmethod
    def play_music(event=None):
        if SoundSystem.IS_MUSIC_LOADED:
            if SoundSystem.IS_MUSIC_PLAYED:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play(-1)
                SoundSystem.IS_MUSIC_PLAYED = True
        else:
            get_debugger().error("Aucune musique n'a été chargée")

    @staticmethod
    def pause_music(event=None):
        pygame.mixer.music.pause()

    @staticmethod
    def reset_music():
        pygame.mixer.music.play(loops=-1, start=0.0)

    @staticmethod
    def set_music_volume(value: int):
        """
        Method to update game music volume

        Args:
            - value : int (new volume value between 0 and 1)
        """

        pygame.mixer.music.set_volume(value)

    @staticmethod
    def set_sounds_volume(value: int):
        """
        Method to update game sounds volume

        Args:
            - value : int (new volume value between 0 and 1)
        """

        for sound in SoundSystem.SOUNDS.values():
            sound.set_volume(value)

    @staticmethod
    def play_button_clicked(event: ButtonClickedEvent = None):
        """
        Method to play click sound (static because the world isn't initialized in the menu)
        """

        SoundSystem.SOUNDS["button_clicked"].play()

    def play_arrow_fired(self, event: ArrowFiredEvent):
        SoundSystem.SOUNDS["arrow_fired"].play()

    def play_fireball_fired(self, event: FireballFiredEvent):
        SoundSystem.SOUNDS["fireball_fired"].play()

    def play_victory(self, event: VictoryEvent):
        SoundSystem.SOUNDS["victory"].play()

    def play_death_sound(self, event: DeathEvent):
        """
        Play correct death sound according to entity type
        """

        # Get entity type
        entity_type = esper.component_for_entity(event.entity, EntityType)

        # Play correct sound
        if entity_type == EntityType.BRUTE or entity_type == EntityType.CROSSBOWMAN:
            SoundSystem.SOUNDS["piglin_death"].play()
        elif entity_type == EntityType.GHAST:
            SoundSystem.SOUNDS["ghast_death"].play()

        # On pourra rajouter le bastion si nécessaire et le beacon si implémenté
