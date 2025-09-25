from .position import Position
from core.component import Component

from core.entity import Entity
from components.sprite import Sprite


class Case(Entity):

    types_of_cases = [
        "Lava",
        "Soulsand",
        "Red_netherrack",
        "Blue_netherrack",
        "Netherrack",
    ]  # static list of the possible types for a case

    def __init__(self, coordonates: Position = Position(), type: str = "Netherrack"):
        """Creates a Case from a Position and a type, or from a default Position and type if empty."""
        if type not in Case.types_of_cases:
            raise ValueError(
                f"type must be one of {Case.types_of_cases}"
            )  # returns an error if the type isn't part of the possible types for a case

        components = ()

        if type == "Lava":
            components = (
                Sprite(
                    "assets/images/lava.png",
                    160,
                    160,
                    {"idle": {"down": list(range(1, 20)) + list(range(19, 0, -1))}},
                    0.05,
                ),
                coordonates,
            )

            super().__init__(components=components)

        self.coordonates = coordonates  # copies the provided position in coordonates
        self.type = type  # copies the provided type in type

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

    def getType(self) -> str:
        """Returns the type of the case."""
        return self.type

    def setPosition(self, value: Position) -> None:
        """Sets the position of the case to be as the one provided."""
        self.coordonates = value

    def setType(self, value: str) -> None:
        """Sets the position of the case to be as the one provided."""
        if type not in Case.types_of_cases:
            raise ValueError(
                f"type must be one of {Case.types_of_cases}"
            )  # returns an error if the type isn't part of the possible types for a case
        self.type = value

    def __str__(self):
        """Returns a string representation of the case using its position and type.\n"""
        return f"Case of coordonates ({self.coordonates.getX()}, {self.coordonates.getY()}), and of type {self.type}.\n"
