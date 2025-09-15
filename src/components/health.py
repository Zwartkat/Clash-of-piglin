class Health :
    
    remaining : int
    full : int
    
    def __init__(self, health : int):
        self.remaining = health
        self.full = health