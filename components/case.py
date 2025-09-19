from .position import Position

class Case :
    
    types_of_cases = ["Lava", "Soulsand", "Red_netherrack", "Blue_netherrack", "Netherrack"]

    def __init__(self, coordonates : Position = Position(1, 1), type : str = "Netherrack"):
        if type not in Case.types_of_cases:
            raise ValueError(f"type must be one of {Case.types_of_cases}")
        self.coordonates = coordonates
        self.type = type
        
    @classmethod
    def initFromModel(cls, model):
        if not isinstance(model, cls):
            raise TypeError("model must be a Case instance")
        return cls(Position(model.getPosition()), model.getType())

    def getPosition(self) -> Position :
        return self.coordonates
    
    def getType(self) -> str :
        return self.type
    
    def setPosition(self, value : Position) -> None :
        self.coordonates = value
        
    def setType(self, value : str) -> None :
        if type not in Case.types_of_cases:
            raise ValueError(f"type must be one of {Case.types_of_cases}")
        self.type = value
        
    def __str__(self):
        return f"Case of coordonates ({self.coordonates.getX()}, {self.coordonates.getY()}), and of type {self.type}.\n"