import asyncio
import os
import os.path
from typing import Optional

from discord_api.discordClient import DiscordAPI, initialize_discord_client
from discord_api.discordClientUtils import find_discord_member, DiscordUtils
from excel import (
    SiegeExcelSheets,
    export_siege_sheet,
    compare_assignment_changes,
    extract_member_count_from_assignments_sheet,
    extract_members_from_members_sheet,
    extract_members_from_reserves_sheet,
    extract_positions_from_excel,
    extract_date_from_filename,
)
from .siege_planner import AssignmentPlanner, Position
from .siege_utils import build_changeset, load_recent_siege_files


root = "E:\\My Files\\Games\\Raid Shadow Legends\\siege\\"


async def   main_function(guild_name: str, send_dm: bool, post_message: bool, force_accept: bool = False) -> None:
    """
    Main function to process siege assignments, post images/messages, and optionally send DMs.

    Args:
        guild_name (str): The name of the guild.
        send_dm (bool): Whether to send DMs to members about assignment changes.
        post_message (bool): Whether to post assignment images and messages to Discord channels.
        force_accept (bool): If True, force accept the two most recent siege files without confirmation. Does not ovveride file validity.
    Returns:
        None
    """
    bot_token = DiscordUtils.get_bot_token()
    discord_client = await initialize_discord_client(guild_name, bot_token)

    # Load the most recent siege files
    siege_planner = AssignmentPlanner(root)
    siege_planner.most_recent_file, siege_planner.second_most_recent_file = load_recent_siege_files(root, force_accept)
    SiegeExcelSheets.set_member_count(extract_member_count_from_assignments_sheet(root, siege_planner.most_recent_file.file_name))

    assignment_sheet_image = export_siege_sheet(root, SiegeExcelSheets.assignment_sheet, siege_planner.most_recent_file.file_name, root)
    reserves_sheet_image = export_siege_sheet(root, SiegeExcelSheets.reserves_sheet, siege_planner.most_recent_file.file_name, root)

    members_set = extract_members_from_members_sheet(root, siege_planner.most_recent_file.file_name)
    siege_assignments = extract_members_from_reserves_sheet(root, siege_planner.most_recent_file.file_name)

    # Map siege_assignments by name for quick lookup
    assignment_map = {a.name: a for a in siege_assignments}
    for member in members_set:
        assignment = assignment_map.get(member.name)
        if assignment:
            member.siege_assignment = assignment

    if post_message:
        channel = "clan-siege-assignment-images"
        try:
            assignment_response = await discord_client.post_image(channel, assignment_sheet_image)
            reserves_response = await discord_client.post_image(channel, reserves_sheet_image)
        except Exception as e:
            raise RuntimeError(f"Failed to post images to Discord: {e}")

        channel = "clan-siege-assignments"
        message = "--------------------------------------------------------------" \
                  f"\n**Siege Assignments - {siege_planner.most_recent_file.date}**\n" \
                  "--------------------------------------------------------------"
        try:
            await discord_client.post_message(channel, message)
            await discord_client.post_message(channel, assignment_response.attachments[0].url)
            await discord_client.post_message(channel, reserves_response.attachments[0].url)
        except Exception as e:
            raise RuntimeError(f"Failed to send messages to Discord channel '{channel}': {e}")

    # Fetch all members from the guild
    members = await discord_client.get_guild_members()
    nickname_to_member = {m.get('nickname') or m.get('discord_name'): m for m in members}

    # Get changed assignments
    changed_assignments = compare_assignment_changes(siege_planner.old_file_path, siege_planner.current_file_path)

    # Compute unchanged assignments
    old_assignments = dict(extract_positions_from_excel(siege_planner.old_file_path))
    new_assignments = dict(extract_positions_from_excel(siege_planner.current_file_path))
    unchanged_assignments = get_unchanged_positions(old_assignments, new_assignments)

    # Map Discord members by nickname to changed assignments and print
    send_all = send_siege_assignments(discord_client, changed_assignments, unchanged_assignments, siege_planner.most_recent_file.date, send_dm, members_set)
    await send_all()

async def fetch_channel_members_function(guild_name):
    bot_token = DiscordUtils.get_bot_token()
    discord_client = await initialize_discord_client(guild_name, bot_token)

    members = await discord_client.get_guild_members()

    print("Members in the channel:")
    for member in members:
        print(f"Username: {member['username']}, Nickname: {member['nickname']}")

def format_assignment_summary(assignments: dict, set_reserve=None, attack_day=None) -> str:
    """
    Format a multi-line table for assignment changes, including reserve and attack day columns.

    Args:
        assignments (dict): Dict with 'old', 'new', and 'unchanged' assignment lists.
        set_reserve (bool, optional): Whether the member is a reserve.
        attack_day (int, optional): The member's attack day.

    Returns:
        str: Formatted table string.
    """
    old = assignments['old']
    new = assignments['new']
    unchanged = assignments['unchanged']
    max_len = max(len(old), len(new), len(unchanged), 1)
    old_list = [str(pos) for pos in old] + [''] * (max_len - len(old))
    new_list = [str(pos) for pos in new] + [''] * (max_len - len(new))
    unchanged_list = [str(pos) for pos in unchanged] + [''] * (max_len - len(unchanged))
    reserve_str = 'Yes' if set_reserve else 'No' if set_reserve is not None else 'Unknown'
    attack_day_str = str(attack_day) if attack_day is not None else 'Unknown'
    reserve_col = [reserve_str] + [''] * (max_len - 1)
    attack_day_col = [attack_day_str] + [''] * (max_len - 1)
    header = f"{'Old':<25} | {'New':<25} | {'Unchanged':<25} | {'Reserve':<8} | {'Attack Day':<10}"
    sep = '-' * len(header)
    rows = [f"{old_list[i]:<25} | {new_list[i]:<25} | {unchanged_list[i]:<25} | {reserve_col[i]:<8} | {attack_day_col[i]:<10}" for i in range(max_len)]
    return '\n'.join([header, sep] + rows)

def send_siege_assignments(
    discord_client,
    changed_assignments,
    unchanged_assignments,
    siege_date,
    send_dm: bool = False,
    members_set=None
):
    """
    Sends DMs to Discord members with all their siege assignment changes in a single message and prints the changes.

    Args:
        discord_client: The DiscordAPI client instance.
        changed_assignments (dict): Mapping of member name to (old_pos, new_pos) tuples.
        unchanged_assignments (dict): Mapping of member name to unchanged Position assignments.
        siege_date (str): The date of the siege (YYYY-MM-DD).
        send_dm (bool): Whether to send DMs to members about assignment changes.
        members_set (List[Member], optional): List of Member objects with siege_assignment info.
    """
    print("Changed Siege Assignments:")
    async def send_all():
        member_changes = build_changeset(changed_assignments, unchanged_assignments)
        discord_members = await discord_client.get_guild_members_disc()
        member_lookup = {m.name: m for m in members_set} if members_set else {}
        for member_name, assignments in member_changes.items():
            member_obj = find_discord_member(discord_members, member_name)
            member_info = member_lookup.get(member_name)
            set_reserve = None
            attack_day = None
            if member_info and getattr(member_info, 'siege_assignment', None):
                set_reserve = member_info.siege_assignment.set_reserve
                attack_day = member_info.siege_assignment.attack_day
            if member_obj:
                summary = format_assignment_summary(assignments, set_reserve, attack_day)
                print(
                    f"Discord: {getattr(member_obj, 'name', '')} (Nick: {getattr(member_obj, 'nick', '')}) | Member: {member_name}\n{summary}"
                )
                if send_dm:
                    try:
                        await asyncio.sleep(1)
                        await send_siege_assignment_dm(
                            discord_client,
                            member_obj,
                            assignments,
                            siege_date,
                            set_reserve=set_reserve,
                            attack_day=attack_day
                        )
                    except Exception as e:
                        print(f"Failed to DM {member_name}: {e}")
            else:
                if assignments['old']:
                    for old_pos in assignments['old']:
                        print(f"Member: {member_name} | Removed: {old_pos} (No Discord match)")
                if assignments['new']:
                    for new_pos in assignments['new']:
                        print(f"Member: {member_name} | Added: {new_pos} (No Discord match)")
                for unchanged_pos in assignments['unchanged']:
                    print(f"Member: {member_name} | Unchanged: {unchanged_pos} (No Discord match)")
    return send_all

def send_siege_assignment_dm(discord_client, member_obj, assignments, siege_date, set_reserve=None, attack_day=None):
    """
    Sends a DM to a Discord member with their siege assignment changes, reserve status, attack day, and siege date.

    Args:
        discord_client: The DiscordAPI client instance.
        member_obj: The discord.Member object to DM.
        assignments (dict): Dict with 'old', 'new', and 'unchanged' assignment lists.
        siege_date (str): The date of the siege (YYYY-MM-DD).
        set_reserve (bool, optional): Whether the member is a reserve.
        attack_day (int, optional): The member's attack day.
    """
    disclaimer = (
        ":warning: **This bot is a work in progress. Please verify assignments manually if needed.** :warning:\n"
    )
    title = f"[1MOM] Masters of Magicka Siege Assignment ({siege_date})"
    reserve_str = 'Yes' if set_reserve else 'No' if set_reserve is not None else 'Unknown'
    attack_day_str = str(attack_day) if attack_day is not None else 'Unknown'
    member_info = (
        f"**Have Reserve Set:** {reserve_str}\n"
        f"**Attack Day:** {attack_day_str}\n"
    )
    # Organize assignments into categories
    old = assignments['old']
    new = assignments['new']
    unchanged = assignments['unchanged']

    # Only include non-empty categories
    sections = []
    if unchanged:
        unchanged_lines = '\n'.join(f"- {discord_formatter(pos)}" for pos in unchanged)
        sections.append(f":shield: ** No Change ** :shield:\n{unchanged_lines}")
    if old:
        old_lines = '\n'.join(f"- {discord_formatter(pos)}" for pos in old)
        sections.append(f":x: ** Remove From ** :x:\n{old_lines}")
    if new:
        new_lines = '\n'.join(f"- {discord_formatter(pos)}" for pos in new)
        sections.append(f":crossed_swords: ** Set At ** :crossed_swords:\n{new_lines}")
    if not sections:
        assignments_section = "*No assignments to display.*"
    else:
        assignments_section = '\n\n'.join(sections)

    dm_message = (
        f"{disclaimer}\n"
        f"**{title}**\n\n"
        f"{member_info}\n"
        f"{assignments_section}\n"
    )
    return discord_client.send_message(member_obj, dm_message)

def get_unchanged_positions(old_assignments: dict, new_assignments: dict) -> dict:
    """
    Returns a dictionary of members whose assignments have not changed between two assignment mappings.

    Args:
        old_assignments (dict): Mapping of Position to member from the old assignments.
        new_assignments (dict): Mapping of Position to member from the new assignments.

    Returns:
        dict: Mapping of member name to a list of unchanged Position objects.
    """
    unchanged_assignments = {}
    for new_pos, member in new_assignments.items():
        old_member = old_assignments.get(new_pos)
        if old_member is not None and old_member == member:
            if member not in unchanged_assignments:
                unchanged_assignments[member] = [new_pos]
            else:
                unchanged_assignments[member].append(new_pos)
    return unchanged_assignments

def get_latest_siege_assignments() -> Optional[str]:
    """
    Scans the root directory for the most recent siege assignment Excel file based on the date in the filename.

    Returns:
        Optional[str]: The path to the most recent siege assignment Excel file, or None if not found.
    """
    latest_file = None
    latest_date = None
    for filename in os.listdir(root):
        date_str = extract_date_from_filename(filename)
        if date_str:
            try:
                year, month, day = map(int, date_str.split('-'))
                file_date = (year, month, day)
            except ValueError:
                continue
            if latest_date is None or file_date > latest_date:
                latest_date = file_date
                latest_file = filename
    if latest_file:
        return os.path.join(root, latest_file)
    return None

def print_assignments() -> None:
    """
    Loads the latest siege assignment Excel file, extracts positions, and prints them to the console.

    Returns:
        None
    """
    file_path = get_latest_siege_assignments()
    if not file_path:
        print("No siege assignment Excel file found.")
        return
    positions = extract_positions_from_excel(file_path)
    print("Assignments:")
    for position, member in positions:
        print(f"Member: {member} -> {position}")

def discord_formatter(position: Position) -> str:
    """
    Format a siege assignment position for Discord with color-coded building name and structure:
    Building Name # / Group # / Position # (Post Condition if applicable)
    If group is None, omit it. Building name is colored by type.
    """
    # Discord does not support true color, but we can use code blocks for color hints or emoji
    building_colors = {
        'Stronghold': ':red_circle:',
        'Defense Tower': ':green_circle:',
        'Mana Shrine': ':yellow_circle:',
        'Magic Tower': ':blue_circle:',
        'Post': ':white_circle:'
    }
    color = building_colors.get(position.building, '')
    building = f"{color} {position.building}" if color else position.building
    if getattr(position, 'building_number', None) is not None:
        building = f"{building} {position.building_number}"
    parts = [building]
    if getattr(position, 'group', None) is not None:
        parts.append(f"Group {position.group}")
    if getattr(position, 'position', None) is not None and position.building != 'Post':
        parts.append(f"Pos {position.position}")
    # Post condition (if any)
    post_condition = getattr(position, 'post_condition', None)
    if post_condition:
        parts.append(f"({post_condition})")
    return ' / '.join(parts)

