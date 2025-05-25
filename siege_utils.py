from collections import namedtuple
from excel import get_recent_siege_files, siege_file


def build_changeset(changed_assignments: dict, unchanged_assignments: dict) -> dict:
    """
    Builds a changeset dictionary for all members, including old, new, and unchanged assignments.

    Args:
        changed_assignments (dict): Mapping of member name to dicts with 'old' and 'new' lists of Position objects.
        unchanged_assignments (dict): Mapping of member name to a list of unchanged Position objects.

    Returns:
        dict: Mapping of member name to a dict with 'old', 'new', and 'unchanged' lists of Position objects.
    """
    member_changes = {}
    for member_name, changes in changed_assignments.items():
        if member_name not in member_changes:
            member_changes[member_name] = {"old": [], "new": [], "unchanged": []}
        member_changes[member_name]["old"].extend(changes.get("old", []))
        member_changes[member_name]["new"].extend(changes.get("new", []))
    for member_name, unchanged_pos in unchanged_assignments.items():
        if member_name not in member_changes:
            member_changes[member_name] = {"old": [], "new": [], "unchanged": []}
        member_changes[member_name]["unchanged"].extend(unchanged_pos)
    return member_changes

def format_siege_date(date_str):
    """
    Convert a date string from MM/DD/YYYY to YYYY-MM-DD format.
    """
    month, day, year = date_str.split('/')
    return f"{month}_{day}_{year}"

def get_siege_file_name(date: str):
    """
    Generate the file name for the siege based on the date.
    """
    formatted_date = format_siege_date(date)
    return f"clan_siege_{formatted_date}.xlsm"



def load_recent_siege_files(root, skip_confirmation=False) -> tuple[siege_file, siege_file]:
    """
    Load and optionally confirm the two most recent siege files with user input.

    Args:
        skip_confirmation (bool): If True, skips user confirmation prompt

    Returns:
        tuple: Tuple containing most recent and second most recent file tuples (filename, date)

    Raises:
        SystemExit: If user does not confirm file selection when confirmation is required
    """
    
    most_recent_file, second_most_recent_file = get_recent_siege_files(root)

    # Always print the files found
    print(f"Most recent file (upcoming siege): {most_recent_file[0]} with date {most_recent_file[1]}")
    print(f"Second most recent file (last siege): {second_most_recent_file[0]} with date {second_most_recent_file[1]}")

    if not skip_confirmation:
        confirmation = input("Do you want to proceed with these files? (yes/no): ").strip().lower()
        if confirmation not in ['yes', 'y']:
            raise SystemExit("Operation cancelled by the user.")
        
    return most_recent_file, second_most_recent_file