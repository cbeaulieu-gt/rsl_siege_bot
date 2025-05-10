def format_assignment_table(old_assignments: list, new_assignments: list, unchanged_assignments: list) -> str:
    """
    Formats a Discord markdown list comparing unchanged, old, and new assignments.

    Args:
        old_assignments (list): List of old Position assignments.
        new_assignments (list): List of new Position assignments.
        unchanged_assignments (list): List of unchanged Position assignments.

    Returns:
        str: A Discord-formatted markdown list string.
    """
    def assignment_str(pos):
        if pos is None:
            return "-"
        building = pos.building
        building_num = pos.building_number if pos.building_number is not None else ""
        group = pos.group
        position = pos.position if pos.position is not None else ""
        if building.lower() == "post":
            if group is not None:
                return f"{building} {building_num} - Group {group}"
            else:
                return f"{building} {building_num}"
        if group is not None:
            return f"{building} {building_num} - Group {group} - Position {position}"
        else:
            return f"{building} {building_num} - Position {position}"

    unchanged_section = "**No Change (Keep Defenses At):**\n" + "\n".join(f"- {assignment_str(unchanged)}" for unchanged in unchanged_assignments) if unchanged_assignments else ""
    old_section = "**Remove Defenses From:**\n" + "\n".join(f"- {assignment_str(old)}" for old in old_assignments) if old_assignments else ""
    new_section = "**Set New Defenses At:**\n" + "\n".join(f"- {assignment_str(new)}" for new in new_assignments) if new_assignments else ""
    sections = [section for section in [unchanged_section, old_section, new_section] if section]
    return "\n\n".join(sections)
