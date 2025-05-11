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