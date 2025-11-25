from enum import Enum, auto
from enums.entity.entity_type import EntityType
from enums.button_type import ButtonType


class origin(Enum):
    ENTITY = auto()  # ajouté pour simplifier la compréhension
    BUTTON = auto()


class reasons(Enum):
    DEATH = auto()
    ATTACK = auto()
    CLICK = auto()
    RELEASE = auto()


sounds = {
    origin.ENTITY: {
        EntityType.BRUTE: {
            reasons.DEATH: "assets/audio/sounds/pig.wav",
            reasons.ATTACK: "",
        },
        EntityType.CROSSBOWMAN: {
            reasons.DEATH: "assets/audio/sounds/pig.wav",
            reasons.ATTACK: "",
        },
    },
    origin.BUTTON: {
        ButtonType.DEFAULT_BUTTON: {reasons.RELEASE: ""},
        ButtonType.DEFAULT_BUTTON: {reasons.RELEASE: ""},
    },
}
