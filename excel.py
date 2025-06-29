import os
import re
import xlwings as xw
from pdf2image import convert_from_path
from typing import List, Tuple, Optional
from siege.siege_planner import Position, Member, SiegeAssignment
from collections import namedtuple
from logger import get_logger

logger = get_logger(__name__)

siege_file = namedtuple("SiegeFile", ["file_name", "date"])
sheet = namedtuple("Sheet", ["name", "cell_range"])
class SiegeExcelSheets:

    DEFAULT_MEMBER_COUNT = 30
    NUM_ASSIGNMENTS_GROUPS = 39
    ASSIGNMENT_SHEET_OFFSET = 3  # Offset for the assignments sheet
    
    @classmethod
    def set_member_count(cls, count: int):
        """
        Sets the number of members in the Members sheet.
        """
        cls.members_sheet = sheet("Members", f"A1:E{count}")
        cls.assignment_sheet = sheet("Assignments", f"A1:E{count}")
        cls.reserves_sheet = sheet("Reserves", f"A1:D{count}")

    members_sheet = sheet("Members", f"A1:E{DEFAULT_MEMBER_COUNT}")
    assignment_sheet = sheet("Assignments", f"A1:E{NUM_ASSIGNMENTS_GROUPS + ASSIGNMENT_SHEET_OFFSET}")
    reserves_sheet = sheet("Reserves", f"A1:D{DEFAULT_MEMBER_COUNT}")

def compare_sheets_between_workbooks(file_path1, file_path2, sheet_name, cell_range):
    """
    Compare a range of cells between two sheets with the same name in different Excel workbooks.

    :param file_path1: Path to the first Excel workbook.
    :param file_path2: Path to the second Excel workbook.
    :param sheet_name: Name of the sheet to compare.
    :param cell_range: Range of cells to compare (e.g., "A1:D10").
    :return: List of differences as tuples (cell_address, value_in_file1, value_in_file2).
    """
    differences = []

    # Open the Excel workbooks
    app = xw.App(visible=False)  # Run Excel in the background
    wb1 = app.books.open(file_path1)
    wb2 = app.books.open(file_path2)

    try:
        # Access the sheets
        sheet1 = wb1.sheets[sheet_name]
        sheet2 = wb2.sheets[sheet_name]

        # Get the ranges
        range1 = sheet1.range(cell_range).value
        range2 = sheet2.range(cell_range).value

        # Compare the ranges cell by cell
        for row_idx, (row1, row2) in enumerate(zip(range1, range2)):
            for col_idx, (val1, val2) in enumerate(zip(row1, row2)):
                if val1 != val2:
                    cell_address = f"{chr(65 + col_idx)}{row_idx + 1}"  # Convert to cell address
                    differences.append((cell_address, val1, val2))

    finally:
        # Clean up
        wb1.close()
        wb2.close()
        app.quit()
        logger.info(f"Compared sheets '{sheet_name}' between '{file_path1}' and '{file_path2}'. Found {len(differences)} differences.")

    return differences

# Convert the PDF to PNG
def convert_pdf_to_png(pdf_file, output_png):
    images = convert_from_path(pdf_file)
    images[0].save(output_png, 'PNG')  # Save the first page as PNG
    logger.info(f"PDF converted to PNG: {output_png}")

# Example usage

def print_excel_range(file_path, sheet_name, cell_range, output_file):
    # Open the workbook and access the sheet
    wb = xw.Book(file_path)
    sheet = wb.sheets[sheet_name]

    # Set the print area to the specified range
    sheet.api.PageSetup.PrintArea = cell_range

    # Export the print area to an image (or PDF)
    sheet.api.ExportAsFixedFormat(
        Type=0,  # 0 = PDF, 1 = XPS
        Filename=output_file,
        Quality=0,  # 0 = standard
        IncludeDocProperties=True,
        IgnorePrintAreas=False
    )


    # Close the workbook without saving
    wb.close()

    logger.info(f"Range '{cell_range}' from sheet '{sheet_name}' has been printed to '{output_file}'.")


def export_range_as_image(file_path, sheet_name, cell_range, output_image_path):
    """
    Export a range of cells from an Excel workbook as an image using xlwings.

    :param file_path: Path to the Excel workbook.
    :param sheet_name: Name of the worksheet containing the range.
    :param cell_range: Range of cells to export (e.g., "A1:D10").
    :param output_image_path: Path to save the output image (e.g., "output.png").
    """
    # Open the Excel workbook
    app = xw.App(visible=False)  # Run Excel in the background
    wb = app.books.open(file_path)
    sheet = wb.sheets[sheet_name]

    try:
        # Copy the range of cells as a picture
        rng = sheet.range(cell_range)

        # Export the range as a PNG
        rng.to_png(output_image_path)

        logger.info(f"Image saved successfully to: {output_image_path}")
        return output_image_path

    finally:
        # Clean up
        wb.close()
        app.quit()


def export_siege_sheet(root: str, sheet: SiegeExcelSheets, file_name: str, output_dir: str) -> str:
    """
    Exports a specific sheet from the siege Excel file to an image.

    Args:
        root (str): Root directory path containing siege files.
        sheet (SiegeExcelSheets): The sheet to export.
        file_name (str): The name of the Excel file.
        output_dir (str): Directory to save the exported image.

    Returns:
        str: Path to the exported image.
    """
    file_path = os.path.join(root, file_name)
    output_image_path = os.path.join(output_dir, f"{sheet.name}.png")
    export_range_as_image(file_path, sheet.name, sheet.cell_range, output_image_path)
    logger.info(f"Exported siege sheet '{sheet.name}' from '{file_name}' to '{output_image_path}'.")
    return output_image_path

def parse_building_cell(building_cell: str) -> Tuple[str, Optional[int]]:
    """
    Parses the building cell to extract the building name and number.

    Args:
        building_cell (str): The cell value containing building info.

    Returns:
        Tuple[str, Optional[int]]: The building name and optional building number.
    """
    parts = str(building_cell).split()
    if parts and parts[-1].isdigit():
        building_number = int(parts[-1])
        building_name = ' '.join(parts[:-1])
    else:
        building_name = str(building_cell)
        building_number = None
    full_name = get_full_tower_name(building_name)
    return full_name, building_number


def parse_group_cell(group_cell: str, current_group: Optional[str]) -> Optional[int]:
    """
    Parses the group cell to extract the group number.

    Args:
        group_cell (str): The cell value containing group info.
        current_group (Optional[str]): The current group value if cell is empty.

    Returns:
        Optional[int]: The group number or None if not found.
    """
    group = group_cell if group_cell else current_group
    try:
        return int(group) if group is not None else None
    except ValueError:
        return None


def extract_row_positions(row: list, building_name: str, building_number: Optional[int], group_num: Optional[int]) -> List[Tuple[Position, str]]:
    """
    Extracts (Position, member) pairs from a row if members are assigned.

    Args:
        row (list): The row data from Excel.
        building_name (str): The full building name.
        building_number (Optional[int]): The building number.
        group_num (Optional[int]): The group number, or None if not identified.

    Returns:
        List[Tuple[Position, str]]: List of (Position, member) pairs.
    """
    positions = []
    for pos_idx in range(1, 4):
        member = row[pos_idx + 1] if len(row) > pos_idx + 1 else None
        if member and building_name:
            try:
                position = Position(
                    building=building_name,
                    group=group_num,
                    position=pos_idx,
                    building_number=building_number
                )
                positions.append((position, str(member)))
            except Exception as e:
                logger.error(f"Exception occurred while creating Position: {e}")
                continue
    return positions


def extract_positions_from_excel(file_path: str) -> List[Tuple[Position, str]]:
    """
    Extracts a list of (Position, member) pairs from the 'Assignment' sheet of an Excel file.

    Args:
        file_path (str): Path to the Excel workbook.

    Returns:
        List[Tuple[Position, str]]: A list of (Position, member) pairs extracted from the sheet.
    """
    positions: List[Tuple[Position, str]] = []
    app = xw.App(visible=False)
    wb = app.books.open(file_path)
    try:
        sheet = wb.sheets['Assignments']
        data = sheet.range('A1:E100').value  # Adjust range as needed
        current_building_name = None
        current_building_number = None
        current_group = None
        for row in data[1:]:  # Skip header row
            building_cell = row[0]
            group_cell = row[1]
            if building_cell:
                current_building_name, current_building_number = parse_building_cell(building_cell)
            group_num = parse_group_cell(group_cell, current_group)
            if group_num is not None:
                current_group = group_num
            positions.extend(
                extract_row_positions(row, current_building_name, current_building_number, group_num)
            )
    finally:
        wb.close()
        app.quit()
        logger.info(f"Extracted {len(positions)} positions from '{file_path}'.")
    return positions



def get_full_tower_name(alias: str) -> str:
    """
    Maps a tower alias to its full name.

    Args:
        alias (str): The short or partial name of the tower.

    Returns:
        str: The full name of the tower.
    """
    alias_map = {
        'Mana': 'Mana Shrine',
        'Defense': 'Defense Tower',
        'Magic': 'Magic Tower',
    }
    for key, full_name in alias_map.items():
        if alias.startswith(key):
            return full_name
    return alias

def compare_assignment_changes(old_file: str, new_file: str) -> dict[str, dict[str, list[Optional[Position]]]]:
    """
    Compares assignments between two Excel files and returns a dictionary of members with lists of old and new positions (including added or removed assignments).

    Args:
        old_file (str): Path to the old Excel file.
        new_file (str): Path to the new Excel file.

    Returns:
        dict[str, dict[str, list[Optional[Position]]]]: A dictionary where the key is the member name and the value is a dict with 'old' and 'new' lists of positions for changed, added, or removed members.
    """
    old_assignments = extract_positions_from_excel(old_file)
    new_assignments = extract_positions_from_excel(new_file)

    # Build mapping: member -> list of positions
    old_map: dict[str, list[Position]] = {}
    for pos, member in old_assignments:
        old_map.setdefault(member, []).append(pos)
    new_map: dict[str, list[Position]] = {}
    for pos, member in new_assignments:
        new_map.setdefault(member, []).append(pos)

    member_changes: dict[str, dict[str, list[Optional[Position]]]] = {}
    all_members = set(old_map.keys()) | set(new_map.keys())
    for member in all_members:
        old_positions = set(old_map.get(member, []))
        new_positions = set(new_map.get(member, []))
        removed = list(old_positions - new_positions)
        added = list(new_positions - old_positions)
        if removed or added:
            member_changes[member] = {
                'old': removed,
                'new': added
            }
    logger.info(f"Compared assignments between '{old_file}' and '{new_file}'. Found {len(member_changes)} members with changes.")
    return member_changes

def extract_date_from_filename(filename):
    match = re.search(r'clan_siege_(\d{2})_(\d{2})_(\d{4})', filename)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month}-{day}"
    return None

def get_recent_siege_files(root)-> tuple[siege_file]:
    siege_files = []
    for file in os.listdir(root):
        if file.endswith('.xlsm'):
            date_str = extract_date_from_filename(file)
            if date_str:
                siege_files.append(siege_file(file, date_str))

    # Sort files by date in descending order
    siege_files.sort(key=lambda x: x.date, reverse=True)

    if len(siege_files) < 2:
        raise ValueError("Not enough siege files found in the directory.")

    return siege_files[0], siege_files[1]

def extract_members_from_reserves_sheet(root: str, file_name: str) -> List[SiegeAssignment]:
    """
    Extracts a list of SiegeAssignment objects from the 'Reserves' sheet of an Excel file.

    Args:
        root (str): Root directory path containing siege files.
        file_name (str): The name of the Excel file.

    Returns:
        List[SiegeAssignment]: A list of SiegeAssignment objects extracted from the Reserves sheet.
    
    Column mapping:
        A -> Member Name
        B -> Unused
        C -> Set Reserve (indicated by presence of 'X')
        D -> Attack Day (1 or 2)
    """
    file_path = os.path.join(root, file_name)
    siege_assignments: List[SiegeAssignment] = []
    app = xw.App(visible=False)
    wb = app.books.open(file_path)
    
    try:
        reserves_sheet = SiegeExcelSheets.reserves_sheet
        sheet = wb.sheets[reserves_sheet.name]
        data = sheet.range(reserves_sheet.cell_range).value
        
        for row in data[1:]:  # Skip header row
            if not row or len(row) < 4:
                continue
                
            member_name = row[0]
            # Column B is unused (row[1])
            set_reserve_cell = row[2]
            attack_day_cell = row[3]
            
            # Skip rows with no member name
            if not member_name or str(member_name).strip() == '':
                continue
            
            try:
                # Parse Set Reserve - check for presence of 'X' character
                set_reserve = False
                if set_reserve_cell:
                    set_reserve_str = str(set_reserve_cell).strip().upper()
                    set_reserve = 'X' in set_reserve_str
                
                # Parse Attack Day - must be 1 or 2
                attack_day = None
                if attack_day_cell:
                    try:
                        attack_day = int(float(attack_day_cell))  # Handle potential float conversion
                        if attack_day not in (1, 2):
                            logger.warning(f"Invalid attack day {attack_day} for member {member_name}. Skipping member.")
                            continue
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse attack day '{attack_day_cell}' for member {member_name}. Skipping member.")
                        continue
                else:
                    logger.warning(f"No attack day specified for member {member_name}. Skipping member.")
                    continue                # Create SiegeAssignment object
                siege_assignment = SiegeAssignment(
                    name=str(member_name).strip(),
                    attack_day=attack_day,
                    set_reserve=set_reserve
                )
                siege_assignments.append(siege_assignment)
                logger.debug(f"Added SiegeAssignment for member {member_name} (reserve={set_reserve}, attack_day={attack_day})")
                
            except Exception as e:
                logger.error(f"Error creating SiegeAssignment object for {member_name}: {e}")
                continue
                
        logger.info(f"Extracted {len(siege_assignments)} siege assignments from reserves sheet in '{file_name}'.")
    finally:
        wb.close()
        app.quit()
    
    return siege_assignments


def extract_members_from_members_sheet(root: str, file_name: str) -> List[Member]:
    """
    Extracts a list of Member objects from the 'Members' sheet of an Excel file.

    Args:
        root (str): Root directory path containing siege files.
        file_name (str): The name of the Excel file.

    Returns:
        List[Member]: A list of Member objects extracted from the Members sheet.
    
    Column mapping:
        A -> Member Name
        E -> PostRestrictions (comma-separated values)
        All other columns are ignored
    """
    file_path = os.path.join(root, file_name)
    members: List[Member] = []
    app = xw.App(visible=False)
    wb = app.books.open(file_path)
    
    try:
        members_sheet = SiegeExcelSheets.members_sheet
        sheet = wb.sheets[members_sheet.name]
        data = sheet.range(members_sheet.cell_range).value
        
        for row in data[1:]:  # Skip header row
            if not row or len(row) < 1:
                continue
                
            member_name = row[0]
            
            # Skip rows with no member name
            if not member_name or str(member_name).strip() == '':
                continue
            
            try:
                # Parse PostRestrictions from column E (index 4)
                post_restriction = None
                if len(row) > 4 and row[4]:
                    post_restriction_str = str(row[4]).strip()
                    if post_restriction_str:
                        # Split by comma and clean up whitespace
                        post_restriction = [item.strip() for item in post_restriction_str.split(',') if item.strip()]
                        # Set to None if empty list
                        if not post_restriction:
                            post_restriction = None
                  # Create Member object with only name and post_restriction
                # since siege assignment info is not available in the Members sheet
                member = Member(
                    name=str(member_name).strip(),
                    post_restriction=post_restriction
                )
                members.append(member)
                logger.debug(f"Added Member: {member_name} (restrictions={post_restriction})")
                
            except Exception as e:
                logger.error(f"Error creating Member object for {member_name}: {e}")
                continue
                
        logger.info(f"Extracted {len(members)} members from members sheet in '{file_name}'.")
    finally:
        wb.close()
        app.quit()
    
    return members
