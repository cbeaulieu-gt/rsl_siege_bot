class Position:
    """
    Represents a position in the siege.

    Attributes:
        building (str): The name of the building.
        group (Optional[int]): The group assigned to the building (1-6), if specified.
        position (int): The position within the group.
        building_number (Optional[int]): The building number (1-18), if specified.
    """
    VALID_BUILDINGS = {"Stronghold", "Mana Shrine", "Magic Tower", "Defense Tower", "Post"}

    def __init__(self, building: str, position: int, group: int | None = None, building_number: int | None = None) -> None:
        """
        Initializes a Position instance with validation.

        Args:
            building (str): The name of the building.
            position (int): The position within the group.
            group (Optional[int]): The group assigned to the building (1-6), if specified.
            building_number (Optional[int]): The building number (1-18), if specified.

        Raises:
            ValueError: If any of the fields fail validation.
        """
        if building not in self.VALID_BUILDINGS:
            raise ValueError(f"Invalid building: {building}. Must be one of {self.VALID_BUILDINGS}.")
        if group is not None and not (1 <= group <= 6):
            raise ValueError(f"Invalid group: {group}. Must be in the range 1-6 if specified.")
        if not (1 <= position <= 3):
            raise ValueError(f"Invalid position: {position}. Must be in the range 1-3.")
        if building_number is not None and not (1 <= building_number <= 18):
            raise ValueError("building_number must be between 1 and 18 if specified.")
        self.building = building
        self.group = group
        self.position = position
        self.building_number = building_number

    def __repr__(self) -> str:
        """
        Returns a string representation of the Position instance.

        Returns:
            str: A string representation of the position.
        """
        return (f"Position(Building='{self.building}', Group='{self.group}', Position='{self.position}', "
                f"BuildingNumber={self.building_number})")

    def __eq__(self, other) -> bool:
        """
        Checks equality between two Position instances.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if all fields match, False otherwise.
        """
        if not isinstance(other, Position):
            return NotImplemented
        return (
            self.building == other.building and
            self.group == other.group and
            self.position == other.position and
            self.building_number == other.building_number
        )

    def __hash__(self) -> int:
        """
        Returns a hash value for the Position instance based on building, group, position, and building_number.

        Returns:
            int: The hash value of the position.
        """
        return hash((self.building, self.group, self.position, self.building_number))

class AssignmentPlanner:
    """
    Manages member assignments to siege positions.
    """
    def __init__(self) -> None:
        """
        Initializes the AssignmentPlanner with an empty assignment mapping.
        """
        self.assignments: dict[str, Position] = {}

    def set_assignment(self, member: str, position: Position) -> None:
        """
        Assigns a member to a position, replacing any previous assignment.

        Args:
            member (str): The member to assign.
            position (Position): The position to assign the member to.
        """
        self.assignments[member] = position

    def update_assignment(self, member: str, building: str, group: int, position: int) -> None:
        """
        Updates the assignment for a member.

        Args:
            member (str): The member to assign.
            building (str): The building name.
            group (int): The group number.
            position (int): The position number.
        """
        pos = Position(building, position, group)
        self.set_assignment(member, pos)

    def get_assignment(self, member: str) -> Position | None:
        """
        Retrieves the position assigned to a member.

        Args:
            member (str): The member name.

        Returns:
            Optional[Position]: The assigned position or None if not assigned.
        """
        return self.assignments.get(member)

    def clear_assignments(self) -> None:
        """
        Removes all assignments from the planner.
        """
        self.assignments.clear()

    def validate_no_duplicate_positions(self) -> bool:
        """
        Validates that no two members are assigned to the same position.

        Returns:
            bool: True if no duplicates are found, False otherwise.
        """
        seen = set()
        for pos in self.assignments.values():
            key = (pos.building, pos.group, pos.position)
            if key in seen:
                return False
            seen.add(key)
        return True