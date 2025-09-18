from core.component import Component

class Position(Component) :
    ''' 
    Composant who represent the position of an entity 
    
    x : int 
    y : int
    '''
    
    x : int 
    y : int
    
    def __init__(self, x : int = 0, y : int = 0):
        self.x = x
        self.y = y