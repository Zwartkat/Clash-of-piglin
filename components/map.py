from .case import Position, Case

import random

class Map : 
    counter = 0
    list_frequencies = {"Lava" : 11, 
                        "Soulsand" : 10,  
                        "Red_netherrack" : 9, 
                        "Blue_netherrack" : 9,
                        "Netherrack" : 0}
    can_generate_on_base = ["Red_netherrack", "Blue_netherrack"]
    default_block = "Netherrack"
    
    def __init__(self, tab : list[list[Case]] = []):
        counter += 1
        self.tab = tab
        self.index = counter
        
    @classmethod
    def initFromModel(cls, model):
        if not isinstance(model, cls):
            raise TypeError("model must be a Map instance")
        return cls(model.getTab())
    
    def getTab(self) -> list[list[Case]] :
        return self.tab
    
    def getIndex(self) -> int :
        return self.index
    
    def setTab(self, model : list[list[Case]]) -> None :
        self.tab = model
        
    def changeCase(self, model : Case) -> None :
        self.tab[model.coordonates.getX()][model.coordonates.getY()] = model
        
    def generate(self, size : int) -> None : 
        
        self.tab = []
        for i in range(size) :
            line = []
            for j in range(size) :
                line.append(Case(Position(i, j), Map.default_block))
            self.tab.append(line)
            
        total_size = size*size #nombre total de cases
        
        for type in Map.list_frequencies : 
            if Map.list_frequencies[type] > 0 :
                starting_position_found = False
                while starting_position_found == False : 
                    starting_position = Position(random.randint(0, size), random.randint(0, size))
                    if ((not ((starting_position.getX() < round(0.2*size)) and (starting_position.getY() < round(0.2*size))) and not ((round(0.8*size) < starting_position.getX()) and (round(0.8*size) < starting_position.getY()))) or type in Map.can_generate_on_base) :
                        starting_position_found = True
                    
                self.changeCase(Case(starting_position, type))
                placed_tiles = 1
                number_of_tiles_to_place = total_size // (Map.list_frequencies[type])
                if ((round(size*0.45)<=starting_position.getX()<=round(size*0.55)) and (round(size*0.45)<=starting_position.getY()<=round(size*0.55))) :
                    while placed_tiles < number_of_lava_tiles :
                        ...
                else :
                    if (number_of_lava_tiles % 2 == 1) : 
                        number_of_lava_tiles += 1
                    while placed_tiles < (number_of_lava_tiles) :
                        ...
                        
# TODO : 
# - Implémentation de la méthode de Pacou
# - Réfléchir à l'implémentation des blocks can_generate_on_base
