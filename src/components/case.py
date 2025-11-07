from core.config import Config
from core.ecs.entity import Entity

from enums.case_type import CaseType
from enums.entity.animation import Animation
from enums.entity.direction import Direction

from components.rendering.sprite import Sprite
from components.base.position import Position


class Case(Entity):

    def __init__(
        self, coordonates: Position = Position(), type: CaseType = CaseType.NETHERRACK
    ):
        """Creates a Case from a Position and a type, or from a default Position and type if empty."""
        if type not in CaseType:
            raise ValueError(
                f"type must be one of {CaseType}"
            )  # returns an error if the type isn't part of the possible types for a case

        components = ()

        if type == CaseType.LAVA:
            components = (
                Sprite(
                    "assets/images/lava.png",
                    160,
                    160,
                    {
                        Animation.NONE: {
                            Direction.NONE: list(range(1, 20)) + list(range(19, 0, -1))
                        }
                    },
                    0.1,
                    sprite_size=(Config.get("tile_size"), Config.get("tile_size")),
                    default_animation=Animation.NONE,
                    default_direction=Direction.NONE,
                ),
                coordonates,
            )

            super().__init__(components=components)

        self.coordonates = coordonates  # copies the provided position in coordonates
        self.type: CaseType = type  # copies the provided type in type

    @classmethod
    def initFromModel(cls, model):
        """Creates a Case from another Case."""
        if not isinstance(model, cls):
            raise TypeError(
                "model must be a Case instance"
            )  # returns an error if the provided case isn't a case
        return cls(
            Position(model.getPosition()), model.getType()
        )  # creates a case from the position and type of the model

    def getPosition(self) -> Position:
        """Returns the position of the case."""
        return self.coordonates

    def getType(self) -> CaseType:
        """Returns the type of the case."""
        return self.type

    def setPosition(self, value: Position) -> None:
        """Sets the position of the case to be as the one provided."""
        self.coordonates = value

    def setType(self, value: CaseType) -> None:
        """Sets the position of the case to be as the one provided."""
        if type not in CaseType:
            raise ValueError(
                f"type must be one of {CaseType}"
            )  # returns an error if the type isn't part of the possible types for a case
        self.type = value

    def __str__(self):
        """Returns a string representation of the case using its position and type.\n"""
        return f"Case of coordonates ({self.coordonates.getX()}, {self.coordonates.getY()}), and of type {self.type}.\n"
