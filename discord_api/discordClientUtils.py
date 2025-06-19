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

import configparser
import json
import os
import string

def load_member_discord_map(json_path: str = 'data\member_discord_map.json') -> dict:
    """
    Loads the member-to-discord username mapping from a JSON file.

    Args:
        json_path (str): Path to the JSON file.

    Returns:
        dict: Mapping of assignment member names to Discord usernames.
    """
    if not os.path.exists(json_path):
        return {}
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _normalize_discord_name(s: str) -> str:
    """
    Normalizes a string for Discord member matching by removing punctuation and converting to lowercase.

    Args:
        s (str): The string to normalize.

    Returns:
        str: The normalized string.
    """
    if not s:
        return ''

    return ''.join(c for c in s.lower() if c not in string.punctuation).strip()


def _update_member_map(member_map: dict, member_name: str, discord_name: str, json_path: str) -> None:
    """
    Updates the member map JSON file with a new mapping.

    Args:
        member_map (dict): The current member map.
        member_name (str): The assignment member name.
        discord_name (str): The Discord username to map.
        json_path (str): Path to the JSON mapping file.
    """
    member_map[member_name] = discord_name
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(member_map, f, indent=2)


def find_discord_member(discord_members: list, member_name: str, json_path: str = 'data\member_discord_map.json') -> object:
    """
    Attempts to find the best matching discord.Member object for a given member name and discord_member_info.
    Tries to load from a static JSON mapping first, then falls back to heuristics. If fallback is used, adds the member to the JSON file.

    Args:
        discord_members (list): List of discord.Member objects.
        discord_member_info (dict): Discord member info dict (from nickname_to_member).
        member_name (str): The member name from assignments.
        json_path (str): Path to the JSON mapping file.

    Returns:
        object: The matching discord.Member object, or None if not found.
    """
    def get_exact_match(m, discord_member_info):
        """
        Checks for an exact match on normalized nickname, discord_name, or global_name, but does not match if the target is an empty string.

        Args:
            m: The discord.Member object.
            target_nick (str): Normalized nickname to match.
            target_user (str): Normalized discord_name to match.
            target_global (str): Normalized global_name to match.

        Returns:
            bool: True if an exact match is found and the target is not empty, False otherwise.
        """
        member_name_norm = _normalize_discord_name(member_name)

        if _normalize_discord_name(getattr(m, 'nick', '')) == member_name_norm:
            return True
        if _normalize_discord_name(getattr(m, 'discord_name', '')) == member_name_norm:
            return True
        if _normalize_discord_name(getattr(m, 'global_name', '')) == member_name_norm:
            return True
        return False
    
    member_map = load_member_discord_map(json_path)
    discord_name = member_map.get(member_name)
    if discord_name:
        for m in discord_members:
            if getattr(m, 'name', '').lower() == discord_name.lower():
                return m

    # Try direct match on nickname or username
    for m in discord_members:
        if get_exact_match(m, member_name):
            if member_name not in member_map or not member_map[member_name]:
                _update_member_map(member_map, member_name, getattr(m, 'name', ''), json_path)
            return m
        
    # If no match, add member with blank value
    if member_name not in member_map:
        _update_member_map(member_map, member_name, "", json_path)
    return None


def get_guild_id(guild_name):
    config = configparser.ConfigParser()
    config.read('guild_config.ini')

    if guild_name in config['Guilds']:
        return config['Guilds'][guild_name]
    else:
        raise ValueError(f"Guild name '{guild_name}' not found in configuration.")


class DiscordUtils:
    @classmethod
    def get_bot_token(cls) -> str:
        """
        Retrieves the Discord bot token from the RAID_BOT_TOKEN environment variable.
        Returns:
            str: The bot token.
        Raises:
            EnvironmentError: If the environment variable is not set.
        """
        import os
        bot_token = os.environ.get("RAID_BOT_TOKEN")
        if not bot_token:
            raise EnvironmentError("RAID_BOT_TOKEN environment variable is not set.")
        return bot_token

