from core.component import Component

class Velocity(Component):
    ''' Composant who represent the velocity of an entity '''
    
    x : float
    y : float
    
    def __init__(self, x : int = 0, y : int = 0):
        self.x = x
        self.y = y