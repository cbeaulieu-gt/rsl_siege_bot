import asyncio
import os.path
from collections import namedtuple
import configparser
import re
import string

import click
from discord_api.discordClient import DiscordAPI
from discord_api.discordClientUtils import find_discord_member
from excel import export_range_as_image, compare_sheets_between_workbooks
from config import *
from siege_planner import Position
from siege_utils import build_changeset


sheet = namedtuple("Sheet", ["name", "cell_range"])

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

def export_siege_sheet(path: str, xl_sheet: sheet) -> str:
    output_file = os.path.join(path, f"{str.lower(xl_sheet.name)}.png")  # Save as PDF (images are not natively supported in xlwings)
    assignments_image_path = export_range_as_image(current_file_path, xl_sheet.name, xl_sheet.cell_range, output_file)
    return assignments_image_path

config = configparser.ConfigParser()
config.read('guild_config.ini')

def get_guild_id(guild_name):
    if guild_name in config['Guilds']:
        return config['Guilds'][guild_name]
    else:
        raise ValueError(f"Guild name '{guild_name}' not found in configuration.")

root = "E:\\My Files\\Games\\Raid Shadow Legends\\siege\\"

def extract_date_from_filename(filename):
    match = re.search(r'clan_siege_(\d{2})_(\d{2})_(\d{4})', filename)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month}-{day}"
    return None

def get_recent_siege_files(root):
    siege_files = []
    for file in os.listdir(root):
        if file.endswith('.xlsm'):
            date_str = extract_date_from_filename(file)
            if date_str:
                siege_files.append((file, date_str))

    # Sort files by date in descending order
    siege_files.sort(key=lambda x: x[1], reverse=True)

    if len(siege_files) < 2:
        raise ValueError("Not enough siege files found in the directory.")

    return siege_files[0], siege_files[1]  # Most recent and second most recent

# Scan the root folder for siege files
most_recent_file, second_most_recent_file = get_recent_siege_files(root)

# Confirm with the user
print(f"Most recent file (upcoming siege): {most_recent_file[0]} with date {most_recent_file[1]}")
print(f"Second most recent file (last siege): {second_most_recent_file[0]} with date {second_most_recent_file[1]}")

confirmation = input("Do you want to proceed with these files? (yes/no): ").strip().lower()
if confirmation not in ['yes', 'y']:
    raise SystemExit("Operation cancelled by the user.")

# Assign file paths
current_file_path = os.path.join(root, most_recent_file[0])
old_file_path = os.path.join(root, second_most_recent_file[0])

assignment_sheet = sheet("Assignments", "A1:E42")
reserves_sheet = sheet("Reserves", "A1:D28")

async def initialize_discord_client(guild_name, bot_token):
    guild_id = get_guild_id(guild_name)
    print(f"Using GUILDID: {guild_id}")
    discord_client = DiscordAPI(guild_id, bot_token=bot_token)

    await discord_client.start_bot()  # Start the bot in the background
    await discord_client.wait_until_ready()

    return discord_client

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

    if post_message:
        assignment_sheet_image = export_siege_sheet(root, assignment_sheet)
        reserves_sheet_image = export_siege_sheet(root, reserves_sheet)

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
    from excel import compare_assignment_changes
    changed_assignments = compare_assignment_changes(old_file_path, current_file_path)

    # Compute unchanged assignments
    from excel import extract_positions_from_excel
    old_assignments = dict(extract_positions_from_excel(old_file_path))
    new_assignments = dict(extract_positions_from_excel(current_file_path))
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

def send_siege_assignments(discord_client, nickname_to_member, changed_assignments, unchanged_assignments, send_dm: bool = False):
    """
    Sends DMs to Discord members with all their siege assignment changes in a single message and prints the changes.

    Args:
        discord_client: The DiscordAPI client instance.
        nickname_to_member (dict): Mapping of member nickname/username to Discord member info.
        changed_assignments (dict): Mapping of member name to (old_pos, new_pos) tuples.
        unchanged_assignments (dict): Mapping of member name to unchanged Position assignments.
    """
    from discord_api.discordClientUtils import format_assignment_table
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
    from discord_api.discordClientUtils import format_assignment_table
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

from excel import extract_positions_from_excel
import os
import re
from typing import Optional, List, Tuple

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

