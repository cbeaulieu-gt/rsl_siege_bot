import os.path
from collections import namedtuple

from discord_api.discord import post_image, post_message, format_discord_link
from excel import export_range_as_image, compare_sheets_between_workbooks

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

root = "E:\\My Files\\Games\\Raid Shadow Legends\\siege\\data\\"

last_siege_date = "04/15/2025"  # Replace with your date
upcoming_siege_date = "04/29/2025"  # Replace with your date

assignment_sheet = sheet("Assignments", "A1:E42")
reserves_sheet = sheet("Reserves", "A1:D28")

old_file_path = os.path.join(root, get_siege_file_name(last_siege_date)) # Path to the Excel file
current_file_path = os.path.join(root, get_siege_file_name(upcoming_siege_date)) # Path to the Excel file

assignment_sheet_image = export_siege_sheet(root, assignment_sheet)
reserves_sheet_image = export_siege_sheet(root, reserves_sheet)

  # Replace with your channel name
channel = "clan-siege-assignment-images"
assignment_response = post_image(assignment_sheet_image, channel)
reserves_response = post_image(reserves_sheet_image, channel)

# formatted_msg_link = format_discord_link(channel, assignment_response.id)
# post_message(f"Siege Assignments Posted here {formatted_msg_link}", channel)
# print(f"Assignment Image URL: {assignment_response.cdn_url}")
# print(f"Reserves Image URL: {reserves_response.cdn_url}")

channel = "clan-siege-assignments"
message = "--------------------------------------------------------------" \
            f"\n**Siege Assignments - {upcoming_siege_date}**\n" \
            "--------------------------------------------------------------"
post_message(message, channel)
post_message(assignment_response.cdn_url, channel)
post_message(reserves_response.cdn_url, channel)


# diff = compare_sheets_between_workbooks(old_file_path, current_file_path, sheet_name, cell_range)
# print(diff)