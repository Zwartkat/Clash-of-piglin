from core.component import Component
from .case import Position, Case
import random

class Map(Component):
    counter = 0
    list_frequencies = {
        "Lava": 11,
        "Soulsand": 10,
        "Red_netherrack": 9,
        "Blue_netherrack": 9,
        "Netherrack": 0,
    }
    can_generate_on_base = ["Red_netherrack", "Blue_netherrack"]
    default_block = "Netherrack"
    neighbours = [[1, 0], [0, -1], [-1, 0], [0, 1]]  # bas,droite,haut,gauche
    # list_restricted_cases = ["Lava"]

    def __init__(self, tab: list[list[Case]] = []):
        Map.counter += 1
        self.tab = tab
        self.index = Map.counter

    @classmethod
    def initFromTab(cls, tab_type: list[list[str]]):
        tab: list[list[Case]] = []
        for i, row in enumerate(tab_type):
            line = []
            for j, type_str in enumerate(row):
                line.append(Case(Position(i, j), type_str))
            tab.append(line)
        return cls(tab)

    @classmethod
    def initFromModel(cls, model):
        if not isinstance(model, cls):
            raise TypeError("model must be a Map instance")
        return cls(model.getTab())

    def getTab(self) -> list[list[Case]]:
        return self.tab

    def getIndex(self) -> int:
        return self.index

    def setTab(self, model: list[list[Case]]) -> None:
        self.tab = model

    def changeCase(self, model: Case) -> None:
        self.tab[model.coordonates.getX()][model.coordonates.getY()] = model

    # def check_path(self, coordonates : Position) -> bool :
    #     ...

    def determinateAvailableNeighbour(
        self, coordonates: Position, size: int, mode: str = "strict"
    ) -> list[Case]:  # type : str,
        list_neighbours: list[Case] = []
        for i in range(len(self.neighbours)):
            if mode == "strict":
                if (
                    (coordonates.getX() + self.neighbours[i][0]) <= round(size * 0.20)
                    and (coordonates.getY() + self.neighbours[i][1])
                    <= round(size * 0.20)
                ) or (
                    (coordonates.getX() + self.neighbours[i][0]) >= round(size * 0.80)
                    and (coordonates.getY() + self.neighbours[i][1])
                    >= round(size * 0.80)
                ):
                    print("neighbour skipped")
                    continue

            if (
                (coordonates.getX() + self.neighbours[i][0]) >= 0
                and (coordonates.getX() + self.neighbours[i][0]) <= size - 1
                and (coordonates.getY() + self.neighbours[i][1] >= 0)
                and (coordonates.getY() + self.neighbours[i][1] <= size - 1)
            ):
                if (
                    self.tab[coordonates.getX() + self.neighbours[i][0]][
                        coordonates.getY() + self.neighbours[i][1]
                    ].getType()
                    == self.default_block
                ):
                    # if type not in self.list_restricted_cases or self.check_path(Position(coordonates.getX() + self.neighbours[i][0], coordonates.getY()+ self.neighbours[i][1])) == True :
                    list_neighbours.append(
                        self.tab[coordonates.getX() + self.neighbours[i][0]][
                            coordonates.getY() + self.neighbours[i][1]
                        ]
                    )

        return list_neighbours

    def generate(self, size: int) -> None:

        self.tab: list[list[Case]] = []
        for i in range(size):
            line = []
            for j in range(size):
                line.append(Case(Position(i, j), Map.default_block))
            self.tab.append(line)

        total_size = size * size  # nombre total de cases

        for type in Map.list_frequencies:
            if Map.list_frequencies[type] > 0:
                
                done = False
                while not done :
                    
                        starting_position_found = False
                        while starting_position_found == False:
                            starting_position = Position(
                                random.randint(0, size - 1), random.randint(0, size - 1)
                            )
                            if self.tab[starting_position.getX()][starting_position.getY()].getType() == Map.default_block :
                                if (
                                    not (
                                        (starting_position.getX() < round(0.2 * size))
                                        and (starting_position.getY() < round(0.2 * size))
                                    )
                                    and not (
                                        (round(0.8 * size) < starting_position.getX())
                                        and (round(0.8 * size) < starting_position.getY())
                                    )
                                ) or type in Map.can_generate_on_base:
                                    starting_position_found = True

                        self.changeCase(Case(starting_position, type))
                        placed_tiles_number = 1
                        placed_tiles = [Case(starting_position, type)]
                        number_of_tiles_to_place = total_size // (Map.list_frequencies[type])
                        if (
                            round(size * 0.45) <= starting_position.getX() <= round(size * 0.55)
                        ) and (
                            round(size * 0.45) <= starting_position.getY() <= round(size * 0.55)
                        ):
                            while placed_tiles_number < number_of_tiles_to_place:
                                
                                candidates = [
                                    case for case in placed_tiles
                                    if self.determinateAvailableNeighbour(case.getPosition(), size, type)
                                ]
                                if not candidates:
                                    print(f"No more available neighbours for type {type}, alterring placement.")
                                    break  # Prevent infinite loop

                                selected_case = random.choice(candidates)    
                                
                                # selected_case = placed_tiles[
                                #     random.randint(0, placed_tiles_number - 1)
                                # ]
                                # print("Selected Case : ", selected_case)
                                list_available_neighbours: list[Case] = (
                                    self.determinateAvailableNeighbour(
                                        selected_case.getPosition(), size, type
                                    )
                                )
                                
                                if len(list_available_neighbours) != 0:
                                    # print("Available neighbours : ", list_available_neighbours)
                                    selected_neighbour = list_available_neighbours[
                                        random.randint(0, len(list_available_neighbours) - 1)
                                    ]
                                    # print("Selected neighbour : ", selected_case)
                                    self.changeCase(
                                        Case(selected_neighbour.getPosition(), type)
                                    )
                                    placed_tiles_number += 1
                                    placed_tiles.append(
                                        Case(selected_neighbour.getPosition(), type)
                                    )
                                    # print("case placed")
                                    
                            done = True
                                    
                        else:
                            if number_of_tiles_to_place % 2 == 1:
                                number_of_tiles_to_place += 1
                            while placed_tiles_number < (number_of_tiles_to_place / 2):
                                
                                candidates = [
                                    case for case in placed_tiles
                                    if self.determinateAvailableNeighbour(case.getPosition(), size, type)
                                ]
                                if not candidates:
                                    print(f"No more available neighbours for type {type}, alterring placement.")
                                    break  # Prevent infinite loop

                                selected_case = random.choice(candidates)
                                
                                # selected_case = placed_tiles[
                                #     random.randint(0, placed_tiles_number - 1)
                                # ]
                                # print("Selected Case (Sym): ", selected_case)
                                list_available_neighbours = self.determinateAvailableNeighbour(
                                    selected_case.getPosition(), size, type
                                )
                                if len(list_available_neighbours) != 0:
                                    # print("Available neighbours (Sym): ", list_available_neighbours)
                                    selected_neighbour = list_available_neighbours[
                                        random.randint(0, len(list_available_neighbours) - 1)
                                    ]
                                    self.changeCase(
                                        Case(selected_neighbour.getPosition(), type)
                                    )
                                    placed_tiles_number += 1
                                    placed_tiles.append(
                                        Case(selected_neighbour.getPosition(), type)
                                    )
                                    # print("case placed (Sym)")

                                    for i in range(placed_tiles_number):
                                        coordonates_tile = placed_tiles[i].getPosition()
                                        if (
                                            self.tab[(size - 1) - coordonates_tile.getX()][
                                                (size - 1) - coordonates_tile.getY()
                                            ].getType()
                                            != type
                                        ):
                                            target = Case(
                                                Position(
                                                    (size - 1) - coordonates_tile.getX(),
                                                    (size - 1) - coordonates_tile.getY(),
                                                ),
                                                type,
                                            )
                                            self.changeCase(target)
                                            # print("symetric case placed")
                            
                            done = True


    def __str__(self) -> str:
        value = "["
        for i in range(len(self.tab)):
            value += "["
            for j in range(len(self.tab[i])):
                type_case = (self.tab[i][j].getType())#[:2]
                value += f"\"{type_case}\","
            value += "],\n"
        value += "]"

        return value


# TODO :
# - Implémentation de la méthode path pour être sûr de ne pas générer de blockage
# - Réfléchir à l'implémentation des blocks can_generate_on_base (plusieurs ilots ?  obligatoires sous les bases ?)
# - Retirer les sécurités de generate
# - Commentaires