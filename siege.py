import asyncio
import os
import os.path
from typing import Optional

from discord_api.discordClient import DiscordAPI, initialize_discord_client
from discord_api.discordClientUtils import find_discord_member, format_assignment_table

from config import *
from excel import (
    SiegeExcelSheets,
    compare_assignment_changes,
    export_siege_sheet,
    extract_positions_from_excel,
    extract_date_from_filename,
)
from siege_planner import AssignmentPlanner, Position
from siege_utils import build_changeset


root = "E:\\My Files\\Games\\Raid Shadow Legends\\siege\\"


async def main_function(guild_name: str, send_dm: bool, post_message: bool) -> None:
    """
    Main function to process siege assignments, post images/messages, and optionally send DMs.

    Args:
        guild_name (str): The name of the guild.
        send_dm (bool): Whether to send DMs to members about assignment changes.
        post_message (bool): Whether to post assignment images and messages to Discord channels.
    Returns:
        None
    """
    discord_client = await initialize_discord_client(guild_name, BOTTOKEN)

    # Load the most recent siege files
    siege_planner = AssignmentPlanner(root)
    most_recent_file, _ = siege_planner.load_recent_siege_files()

    if post_message:
        assignment_sheet_image = export_siege_sheet(root, SiegeExcelSheets.assignment_sheet, most_recent_file, root)
        reserves_sheet_image = export_siege_sheet(root, SiegeExcelSheets.reserves_sheet, most_recent_file, root)

        channel = "clan-siege-assignment-images"
        try:
            assignment_response = await discord_client.post_image(channel, assignment_sheet_image)
            reserves_response = await discord_client.post_image(channel, reserves_sheet_image)
        except Exception as e:
            raise RuntimeError(f"Failed to post images to Discord: {e}")

        channel = "clan-siege-assignments"
        message = "--------------------------------------------------------------" \
                  f"\n**Siege Assignments - {most_recent_file[1]}**\n" \
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
    send_all = send_siege_assignments(discord_client, nickname_to_member, changed_assignments, unchanged_assignments, send_dm)
    await send_all()

async def fetch_channel_members_function(guild_name):
    bot_token = BOTTOKEN
    discord_client = initialize_discord_client(guild_name, BOTTOKEN)

    members = await discord_client.get_guild_members()

    print("Members in the channel:")
    for member in members:
        print(f"Username: {member['username']}, Nickname: {member['nickname']}")

def send_siege_assignments(discord_client, changed_assignments, unchanged_assignments, send_dm: bool = False):
    """
    Sends DMs to Discord members with all their siege assignment changes in a single message and prints the changes.

    Args:
        discord_client: The DiscordAPI client instance.
        nickname_to_member (dict): Mapping of member nickname/username to Discord member info.
        changed_assignments (dict): Mapping of member name to (old_pos, new_pos) tuples.
        unchanged_assignments (dict): Mapping of member name to unchanged Position assignments.
    """
    print("Changed Siege Assignments:")
    async def send_all():
        # Group all changes by member
        member_changes = build_changeset(changed_assignments, unchanged_assignments)

        # Fetch full discord.Member objects
        discord_members = await discord_client.get_guild_members_disc()
        for member_name, assignments in member_changes.items():
            member_obj = find_discord_member(discord_members, member_name)
            if member_obj:
                print(f"Discord: {getattr(member_obj, 'name', '')} (Nickname: {getattr(member_obj, 'nick', '')}) | Member: {member_name} | Changes: Old: {assignments['old']} | New: {assignments['new']} | Unchanged: {assignments['unchanged']}")
                if send_dm:
                    try:
                        # Wait for 1 second to avoid hitting Discord's rate limit
                        await asyncio.sleep(1)
                        await send_siege_assignment_dm(discord_client, member_obj, assignments, most_recent_file[1])
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

def send_siege_assignment_dm(discord_client, member_obj, assignments, siege_date):
    """
    Sends a DM to a Discord member with their siege assignment changes, including unchanged, old, and new assignments, and siege date.

    Args:
        discord_client: The DiscordAPI client instance.
        member_obj: The discord.Member object to DM.
        assignments (dict): Dict with 'old', 'new', and 'unchanged' assignment lists.
        siege_date (str): The date of the siege (YYYY-MM-DD).
    """
    disclaimer = (
        ":warning: **This bot is a work in progress. Please verify assignments manually if needed.** :warning:\n"
    )
    title = f"[1MOM] Masters of Magicka Siege Assignment ({siege_date})"
    table = format_assignment_table(assignments['old'], assignments['new'], assignments['unchanged'])
    dm_message = f"{disclaimer}\n\n**{title}**\n\n{table}"
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

