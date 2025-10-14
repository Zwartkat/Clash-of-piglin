from core.ecs.component import Component
from enums.case_type import CaseType
from components.case import Position, Case
import random


class Map(Component):
    counter = 0  # static counter that allows to differenciate maps with their index
    list_frequencies = {
        CaseType.LAVA: 11,
        CaseType.SOULSAND: 10,
        CaseType.RED_NETHERRACK: 9,
        CaseType.BLUE_NETHERRACK: 9,
        CaseType.NETHERRACK: 0,
    }  # static dictionnary that associate a frequency to all types of blocks, to control the amount of each type of block
    generate_on_base = [
        CaseType.RED_NETHERRACK,
        CaseType.BLUE_NETHERRACK,
    ]  # static list containing the types of blocks that will be used as floor for the bases
    restricted_cases = [
        CaseType.LAVA
    ]  # static list containing the types of blocks that grounded units can't cross (used to check)
    default_block = (
        CaseType.NETHERRACK
    )  # static string stocking the default type of blocks in map generation
    limit_of_generation_for_type = 2  # static number defining the upper limit of the number of group each type can have (outside of impossible generation/base floor generation)
    radius_bases = 0.2  # static float defining the radius of the zone in which the floor around bases will be of the designated type
    radius_center = 0.05  # static float defining the radius of the zone at the center of the map where if a group of block starts generating, it won't be symmetrical
    neighbours = [
        [1, 0],
        [0, -1],
        [-1, 0],
        [0, 1],
    ]  # static list stocking the value to add to the position of a case to get its lower, right, upper and left neighbours respectively.

    def __init__(self, tab: list[list[Case]] = []):
        """Creates a map from a table of Case, or from an empty one by default."""
        Map.counter += 1  # increments the counter of the class
        self.tab = tab  # copies the provided table in tab
        self.index = Map.counter  # copies the current counter of the class as its index

    @classmethod
    def initFromTab(cls, tab_type: list[list[CaseType]]):
        """Creates a map from a table of types."""
        tab: list[list[Case]] = []  # creates a tab
        for i, row in enumerate(tab_type):  # for each line of the table
            line = []  # creates another table for each line
            for j, type in enumerate(row):  # for each type in the line
                line.append(
                    Case(Position(i, j), type)
                )  # adds a case of the corresponding type
            tab.append(line)  # add the line to the tab
        return cls(tab)  # use __init__(tab) to create the instance of map

    @classmethod
    def initFromModel(cls, model):
        """Creates a map from another map, by copying its tab and getting an unique index."""
        if not isinstance(model, cls):  # if the provided model is not a map
            raise TypeError("model must be a Map instance")  # returns an error
        return cls(
            model.getTab()
        )  # else, use  __init__(model.getTab()) to create the instance of map

    def getTab(self) -> list[list[Case]]:
        """Returns the tab of the map."""
        return self.tab

    def getIndex(self) -> int:
        """Returns the index of the map."""
        return self.index

    def setTab(self, model: list[list[Case]]) -> None:
        """Sets the tab of the map to be as the one provided."""
        self.tab = model

    def changeCase(self, model: Case) -> None:
        """Sets the case of tab with the same Position as the model to have the same type as the model."""
        self.tab[model.coordonates.getX()][model.coordonates.getY()] = model

    def getUnrestrictedNeighbours(
        self, coordonates: Position, changing_tile_position: Position, size: int
    ) -> list[Case]:
        """Returns the neighbours of the case of position provided that are accessible. Avoids the neighbour if it a certain position.\n
        coordonates -> Position of the case of which we want the accessible neighbours.
        changing_tile_position -> Position of the tile we consider unaccessible (the tile that might be changed by checkPath).
        size -> Dimensions of the table."""
        neighbours: list[Case] = []  # we create an empty neighbours list

        for i in self.neighbours:  # for each neighbours as defined in self.neighbours
            if (
                (coordonates.getX() + i[0]) >= 0
                and (coordonates.getX() + i[0]) <= size - 1
                and (coordonates.getY() + i[1] >= 0)
                and (coordonates.getY() + i[1] <= size - 1)
            ):  # if the neighbour is within the limits of the table
                if self.tab[coordonates.getX() + i[0]][
                    coordonates.getY() + i[1]
                ].getType() not in self.restricted_cases and not (
                    coordonates.getX() + i[0] == changing_tile_position.getX()
                    and coordonates.getY() + i[1] == changing_tile_position.getY()
                ):  # if the neighbour is accessible and isn't the tile that might be changed by checkPath()
                    neighbours.append(
                        self.tab[coordonates.getX() + i[0]][coordonates.getY() + i[1]]
                    )  # it is added to the list of accessible neighbours

        return neighbours  # returns the list of accessible neighbours

    def checkPath(self, coordonates: Position, size: int) -> bool:
        """Returns True if, accounting for the case of given position turning unaccessible, all accessible cases have at least a path that leads to them.\n
        coordonates -> Position of the case that might become unaccessible.
        size -> Dimensions of the table."""
        cases_to_check: list[Case] = (
            []
        )  # creates list stocking currently accessible cases that needs to be checked as accessible once the case of position given is considered unaccessible
        neighbours: list[Case] = (
            []
        )  # creates a list that stocks the neighbouring cases in waiting of inspections

        for i in range(size):
            for j in range(size):  # for each case in tab
                if self.tab[i][j].getType() not in self.restricted_cases and (
                    i != coordonates.getX() or j != coordonates.getY()
                ):  # if it's accessible and isn't the case that might become unaccessible
                    cases_to_check.append(
                        self.tab[i][j]
                    )  # adds it to the list of cases in need of inspection

        neighbours = self.getUnrestrictedNeighbours(
            cases_to_check[0].getPosition(), coordonates, size
        )  # we start by getting the neighbors of the first case to find
        while (
            neighbours != [] and cases_to_check != []
        ):  # while there's still cases to inspect, or if there is no case left to find
            if (
                neighbours[0] in cases_to_check
            ):  # if the first neighbour is a case to find
                cases_to_check.remove(
                    neighbours[0]
                )  # we remove it from the list of case to found
                for neighbour in self.getUnrestrictedNeighbours(
                    neighbours[0].getPosition(), coordonates, size
                ):  # we add its neighbours to the list of neighbours
                    if (
                        neighbour in cases_to_check and neighbour not in neighbours
                    ):  # if they are accessible and not already in the list of neighbour
                        neighbours.append(neighbour)
            neighbours.remove(neighbours[0])  # finally we remove the first neighbour

        if (
            cases_to_check == []
        ):  # if all accessible cases are found, then they are still accessible with the given case turned unaccessible
            return True
        else:  # else, they aren't
            return False

    def determinateAvailableNeighbour(
        self, coordonates: Position, type: str, size: int
    ) -> list[Case]:
        """Returns a list containing all the neighbour of the case of given position that are available to place a block on.\n
        coordonates -> Position of the case of which we want the available neighbours.
        type -> Type of the block we want to place.
        size -> Dimensions of the table."""
        list_neighbours: list[Case] = (
            []
        )  # creates a list to stocks available neighbours
        for i in range(
            len(self.neighbours)
        ):  # for each of the neighbours defined in self.neighbours
            if (
                (coordonates.getX() + self.neighbours[i][0])
                < round(size * self.radius_bases) - 1
                and (coordonates.getY() + self.neighbours[i][1])
                < round(size * self.radius_bases) - 1
            ) or (
                (coordonates.getX() + self.neighbours[i][0])
                > round(size * (1 - self.radius_bases))
                and (coordonates.getY() + self.neighbours[i][1])
                > round(size * (1 - self.radius_bases))
            ):  # if they are within the radius of a base, skip them
                continue

            if (
                (coordonates.getX() + self.neighbours[i][0]) >= 0
                and (coordonates.getX() + self.neighbours[i][0]) <= size - 1
                and (coordonates.getY() + self.neighbours[i][1] >= 0)
                and (coordonates.getY() + self.neighbours[i][1] <= size - 1)
            ):  # else, if they are within the table
                if (
                    self.tab[coordonates.getX() + self.neighbours[i][0]][
                        coordonates.getY() + self.neighbours[i][1]
                    ].getType()
                    == self.default_block
                ):  # if they are of the default type
                    if (type not in self.restricted_cases) or (
                        self.checkPath(
                            Position(
                                coordonates.getX() + self.neighbours[i][0],
                                coordonates.getY() + self.neighbours[i][1],
                            ),
                            size,
                        )
                        == True
                    ):  # if the type we want to give them isn't restricted or if giving it to them wouldn't result in any case of tab becoming unaccessible
                        list_neighbours.append(
                            self.tab[coordonates.getX() + self.neighbours[i][0]][
                                coordonates.getY() + self.neighbours[i][1]
                            ]
                        )  # we add them to the list of available neighbours

        return list_neighbours  # return the list of available neighbours

    def generate(self, size: int) -> None:
        """Generates a random map with different types of cases, using the wanted size and other static values.\n
        size -> Dimensions of the table."""
        self.tab: list[list[Case]] = []  # reset tab to an empty list
        for i in range(size):
            line = []
            for j in range(size):
                line.append(Case(Position(i, j), self.default_block))
            self.tab.append(
                line
            )  # fill tab to make it a size*size table of only default_type blocks

        total_size = size * size  # calculates the total number of cases in tab

        for type in self.list_frequencies:
            if (
                self.list_frequencies[type] > 0
            ):  # for each type in the dictionnary of frequencies, where frequency is more than one
                max_generation_number_for_type = random.randint(
                    1, self.limit_of_generation_for_type
                )  # we calculate a random number of group that the cases of this type will be split in
                if (
                    type == self.generate_on_base[0]
                ):  # if the current type is the type of the floor of the 1st base
                    for i in range(0, round(self.radius_bases * size) - 1):
                        for j in range(
                            0, round(self.radius_bases * size) - 1
                        ):  # for each case in the radius around the upper left corner of the map
                            self.changeCase(
                                Case(Position(i, j), type)
                            )  # the case is changed to the current type
                    number_of_tiles_to_place = (
                        (total_size // (self.list_frequencies[type]))
                        - (
                            (round(self.radius_bases * size) - 1)
                            * (round(self.radius_bases * size) - 1)
                        )
                    ) / max_generation_number_for_type  # the number of case of the type to place for each group is recalculated to account for those placed under the base
                elif (
                    type == self.generate_on_base[1]
                ):  # if the current type is the type of the floor of the 2nd base
                    for i in range(round((1 - self.radius_bases) * size + 1), size):
                        for j in range(
                            round((1 - self.radius_bases) * size + 1), size
                        ):  # for each case in the radius around the lower right corner of the map
                            self.changeCase(
                                Case(Position(i, j), type)
                            )  # the case is changed to the current type
                    number_of_tiles_to_place = (
                        (total_size // (self.list_frequencies[type]))
                        - (
                            (round(self.radius_bases * size) - 1)
                            * (round(self.radius_bases * size) - 1)
                        )
                    ) / max_generation_number_for_type  # the number of case of the type to place for each group is recalculated to account for those placed under the base
                else:
                    number_of_tiles_to_place = (
                        total_size // (self.list_frequencies[type])
                    ) / max_generation_number_for_type  # the number of case of the type to place for each group is calculated from the frequency of the type, the total number of cases and the number of group for this type

                for i in range(max_generation_number_for_type):  # for each group
                    placed_tiles: list[Case] = (
                        []
                    )  # we create an empty list that stocks the cases placed for this group
                    placed_generation_tile_number = 0  # we create a null counter that counts the number of cases placed for this group
                    done = False  # we create a false boolean
                    while not done:  # while the group isn't finished

                        starting_position_found = False  # we create a false boolean
                        while (
                            starting_position_found == False
                        ):  # while the strating position isn't found
                            starting_position = Position(
                                random.randint(0, size - 1), random.randint(0, size - 1)
                            )  # we get a random case
                            if (
                                self.tab[starting_position.getX()][
                                    starting_position.getY()
                                ].getType()
                                == self.default_block
                            ):  # if it's of the default type
                                if not (
                                    (
                                        starting_position.getX()
                                        < round(self.radius_bases * size) - 1
                                    )
                                    and (
                                        starting_position.getY()
                                        < round(self.radius_bases * size) - 1
                                    )
                                ) and not (
                                    (
                                        round((1 - self.radius_bases) * size)
                                        < starting_position.getX()
                                    )
                                    and (
                                        round((1 - self.radius_bases) * size)
                                        < starting_position.getY()
                                    )
                                ):  # if it's not within the radius of either bases
                                    if (type not in self.restricted_cases) or (
                                        self.checkPath(starting_position, size) == True
                                    ):  # if the type we want to give the case isn't restricted or if giving it to the case wouldn't result in any other case of tab becoming unaccessible
                                        starting_position_found = (
                                            True  # we found a valid starting point
                                        )

                        self.changeCase(
                            Case(starting_position, type)
                        )  # the starting case becomes of the current type
                        placed_generation_tile_number += 1  # the counter increases by 1
                        placed_tiles.append(
                            Case(starting_position, type)
                        )  # the case is put into the list of placed cases for this group
                        if (
                            round(size * (0.5 - (self.radius_center)))
                            <= starting_position.getX()
                            <= round(size * (0.5 + (self.radius_center)))
                        ) and (
                            round(size * (0.5 - (self.radius_center)))
                            <= starting_position.getY()
                            <= round(size * (0.5 - (self.radius_center)))
                        ):  # if the starting point is within the radius around the center of the map, the placement of other tiles in the group will be normal
                            while (
                                placed_generation_tile_number < number_of_tiles_to_place
                            ):  # while all the cases in the group haven't been placed

                                list_available_neighbours: list[list[Case]] = []
                                for case in placed_tiles:
                                    available_neighbours_for_case = (
                                        self.determinateAvailableNeighbour(
                                            case.getPosition(), type, size
                                        )
                                    )
                                    if available_neighbours_for_case != []:
                                        list_available_neighbours.append(
                                            available_neighbours_for_case
                                        )

                                # create a list of candidates which have at least 1 available neighbour
                                if list_available_neighbours == []:
                                    break  # if there is no candidates, will break to choose another starting point

                                selected_neighbour_group = random.choice(
                                    list_available_neighbours
                                )  # choose a random candidate as the case to expend the group from

                                if (
                                    len(selected_neighbour_group) != 0
                                ):  # verifies that it does have at least one available neighbour
                                    selected_neighbour = random.choice(
                                        selected_neighbour_group
                                    )
                                    # select a random neighbour from the list
                                    self.changeCase(
                                        Case(selected_neighbour.getPosition(), type)
                                    )  # change the type of the neighbour to the current type
                                    placed_generation_tile_number += (
                                        1  # the counter increases by 1
                                    )
                                    placed_tiles.append(
                                        Case(selected_neighbour.getPosition(), type)
                                    )  # the case is put into the list of placed cases for this group
                            else:  # if the wanted number of case is reached (or exceeded), the group is completed
                                done = True

                        else:  # if the starting case is not in the center of the map, the group will be of a smaller size and will have a symetrical counterpart
                            if (
                                number_of_tiles_to_place % 2 == 1
                            ):  # if the number of tiles to place is odd, increment it
                                number_of_tiles_to_place += 1

                            while placed_generation_tile_number < (
                                number_of_tiles_to_place / 2
                            ):  # while all the cases for this half of the group haven't been placed

                                candidates = [
                                    case
                                    for case in placed_tiles
                                    if self.determinateAvailableNeighbour(
                                        case.getPosition(), type, size
                                    )
                                ]  # create a list of candidates which have at least 1 available neighbour
                                if not candidates:
                                    break  # if there is no candidates, will break to choose another starting point

                                selected_case = random.choice(
                                    candidates
                                )  # choose a random candidate as the case to expend the group from

                                list_available_neighbours = self.determinateAvailableNeighbour(
                                    selected_case.getPosition(), type, size
                                )  # create a list of the available neighbours of that candidate

                                if (
                                    len(list_available_neighbours) != 0
                                ):  # verifies that it does have at least one available neighbour
                                    selected_neighbour = list_available_neighbours[
                                        random.randint(
                                            0, len(list_available_neighbours) - 1
                                        )
                                    ]  # select a random neighbour from the list
                                    self.changeCase(
                                        Case(selected_neighbour.getPosition(), type)
                                    )  # change the type of the neighbour to the current type
                                    placed_generation_tile_number += (
                                        1  # the counter increases by 1
                                    )
                                    placed_tiles.append(
                                        Case(selected_neighbour.getPosition(), type)
                                    )  # the case is put into the list of placed cases for this group

                            else:  # once a half of the cases of the group are placed
                                for i in range(
                                    placed_generation_tile_number
                                ):  # for each case of the group placed
                                    coordonates_tile = placed_tiles[
                                        i
                                    ].getPosition()  # we get its coordonates
                                    if (
                                        self.tab[(size - 1) - coordonates_tile.getX()][
                                            (size - 1) - coordonates_tile.getY()
                                        ].getType()
                                        != type
                                    ):  # if the opposing case isn't of the current type
                                        target = Case(
                                            Position(
                                                (size - 1) - coordonates_tile.getX(),
                                                (size - 1) - coordonates_tile.getY(),
                                            ),
                                            type,
                                        )
                                        self.changeCase(
                                            target
                                        )  # it is changed into the current type

                                done = True  # then, the group is complete

    def __str__(self) -> str:
        """Returns a string representation of the content of tab for this map.\n"""
        value = "["
        for i in range(len(self.tab)):
            value += "["
            for j in range(len(self.tab[i])):
                type_case = self.tab[i][j]
                value += f'"{type_case}",'
            value += "],\n"
        value += "]"

        return value
