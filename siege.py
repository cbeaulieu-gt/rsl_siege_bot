import asyncio
import os.path
from collections import namedtuple
import configparser
import re

import click
from discord_api.discordClient import DiscordAPI
from excel import export_range_as_image, compare_sheets_between_workbooks
from config import *

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
if confirmation != 'yes':
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

async def main_function(guild_name):
    discord_client = await initialize_discord_client(guild_name, BOTTOKEN)

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

async def fetch_channel_members_function(guild_name):
    bot_token = BOTTOKEN
    discord_client = initialize_discord_client(guild_name, BOTTOKEN)

    members = await discord_client.get_guild_members()

    print("Members in the channel:")
    for member in members:
        print(f"Username: {member['username']}, Nickname: {member['nickname']}")

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