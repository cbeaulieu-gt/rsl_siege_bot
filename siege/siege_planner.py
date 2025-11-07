# filepath: i:\games\raid\siege\siege\siege_planner.py
import os
from typing import Optional, List


class SiegeAssignment:
    """
    Represents a siege assignment for a member.

    Attributes:
        name (str): The name of the member.
        attack_day (int): The attack day (1 or 2).
        set_reserve (bool): Whether the member is set as reserve.
    """

    def __init__(self, name: str, attack_day: int, set_reserve: bool = False) -> None:
        """
        Initializes a SiegeAssignment instance with validation.

        Args:
            name (str): The name of the member.
            attack_day (int): The attack day (1 or 2).
            set_reserve (bool): Whether the member is set as reserve. Defaults to False.

        Raises:
            ValueError: If any of the fields fail validation.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
        if attack_day not in (1, 2):
            raise ValueError("AttackDay must be 1 or 2.")
        if not isinstance(set_reserve, bool):
            raise ValueError("SetReserve must be a boolean value.")
        
        self.name = name
        self.attack_day = attack_day
        self.set_reserve = set_reserve

    def __repr__(self) -> str:
        """
        Returns a string representation of the SiegeAssignment instance.

        Returns:
            str: A string representation of the siege assignment.
        """
        return f"SiegeAssignment(name='{self.name}', attack_day={self.attack_day}, set_reserve={self.set_reserve})"

    def __eq__(self, other) -> bool:
        """
        Checks equality between two SiegeAssignment instances.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if all fields match, False otherwise.
        """
        if not isinstance(other, SiegeAssignment):
            return NotImplemented
        return (
            self.name == other.name and
            self.attack_day == other.attack_day and
            self.set_reserve == other.set_reserve
        )

    def __hash__(self) -> int:
        """
        Returns a hash value for the SiegeAssignment instance based on name, attack_day, and set_reserve.

        Returns:
            int: The hash value of the siege assignment.
        """
        return hash((self.name, self.attack_day, self.set_reserve))


class Member:
    """
    Represents a member with their post restrictions and siege assignment.

    Attributes:
        name (str): The name of the member.
        post_restriction (Optional[List[str]]): Optional list of post restrictions.
        siege_assignment (Optional[SiegeAssignment]): Optional siege assignment information.
    """

    def __init__(self, name: str, post_restriction: Optional[List[str]] = None, siege_assignment: Optional[SiegeAssignment] = None) -> None:
        """
        Initializes a Member instance with validation.

        Args:
            name (str): The name of the member.
            post_restriction (Optional[List[str]]): Optional list of post restrictions. Defaults to None.
            siege_assignment (Optional[SiegeAssignment]): Optional siege assignment. Defaults to None.

        Raises:
            ValueError: If any of the fields fail validation.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Name must be a non-empty string.")
        if post_restriction is not None and not isinstance(post_restriction, list):
            raise ValueError("PostRestriction must be a list of strings or None.")
        if post_restriction is not None and not all(isinstance(item, str) for item in post_restriction):
            raise ValueError("All items in PostRestriction must be strings.")
        if siege_assignment is not None and not isinstance(siege_assignment, SiegeAssignment):
            raise ValueError("SiegeAssignment must be a SiegeAssignment instance or None.")
        
        self.name = name
        self.post_restriction = post_restriction
        self.siege_assignment = siege_assignment

    def __repr__(self) -> str:
        """
        Returns a string representation of the Member instance.

        Returns:
            str: A string representation of the member.
        """
        post_restriction_str = f", post_restriction={self.post_restriction}" if self.post_restriction else ""
        siege_assignment_str = f", siege_assignment={self.siege_assignment}" if self.siege_assignment else ""
        return f"Member(name='{self.name}'{post_restriction_str}{siege_assignment_str})"

    def __eq__(self, other) -> bool:
        """
        Checks equality between two Member instances.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if all fields match, False otherwise.
        """
        if not isinstance(other, Member):
            return NotImplemented
        return (
            self.name == other.name and
            self.post_restriction == other.post_restriction and
            self.siege_assignment == other.siege_assignment
        )

    def __hash__(self) -> int:
        """
        Returns a hash value for the Member instance based on name, post_restriction, and siege_assignment.

        Returns:
            int: The hash value of the member.
        """
        # Convert list to tuple for hashing if post_restriction exists
        post_restriction_tuple = tuple(self.post_restriction) if self.post_restriction else None
        return hash((self.name, post_restriction_tuple, self.siege_assignment))


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
        if group is not None and not (1 <= group <= 9):
            raise ValueError(f"Invalid group: {group}. Must be in the range 1-8 if specified.")
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
    def __init__(self, root: str) -> None:
        """
        Initializes the AssignmentPlanner with an empty assignment mapping.

        Args:
            root (str): Root directory path containing siege files
        """
        self.assignments: dict[str, Position] = {}
        self.root = root
        self.most_recent_file = None
        self.second_most_recent_file = None

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

    @property
    def current_file_path(self) -> str:
        """
        Gets the full path to the current siege file.

        Returns:
            str: Full path to the current siege file
        
        Raises:
            ValueError: If no files have been loaded yet
        """
        if not self.most_recent_file:
            raise ValueError("No siege files have been loaded. Call load_recent_siege_files first.")
        return os.path.join(self.root, self.most_recent_file[0])

    @property 
    def old_file_path(self) -> str:
        """
        Gets the full path to the previous siege file.

        Returns:
            str: Full path to the previous siege file
        
        Raises:
            ValueError: If no files have been loaded yet
        """
        if not self.second_most_recent_file:
            raise ValueError("No siege files have been loaded. Call load_recent_siege_files first.")
        return os.path.join(self.root, self.second_most_recent_file[0])
