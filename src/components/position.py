class Position:

    def __init__(self, x: int = 1, y: int = 1):
        '''Creates a Case from a X and a Y, or from default values if empty.'''
        self.x = x # copies the provided X in X
        self.y = y # copies the provided Y in Y

    @classmethod
    def initFromModel(cls, model):
        '''Creates a Position from another Position.'''
        if not isinstance(model, cls):
            raise TypeError("model must be a Position instance") # returns an error if the provided Position isn't a Position
        return cls(model.x, model.y) # creates a position from the X and Y of the model

    def getX(self) -> int:
        '''Returns the X of the position.'''
        return self.x

    def getY(self) -> int:
        '''Returns the Y of the position.'''
        return self.y

    def setX(self, value: int) -> None:
        '''Sets the X of the position to be as the one provided.'''
        self.x = value

    def setY(self, value: int) -> None:
        '''Sets the Y of the position to be as the one provided.'''
        self.y = value

    def __str__(self):
        '''Returns a string representation of the position using its X and Y.\n'''
        return f"Position of coordonates {self.x}, {self.y}.\n"
