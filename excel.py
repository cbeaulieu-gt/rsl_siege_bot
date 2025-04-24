import xlwings as xw
from pdf2image import convert_from_path


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

    return differences

# Convert the PDF to PNG
def convert_pdf_to_png(pdf_file, output_png):
    images = convert_from_path(pdf_file)
    images[0].save(output_png, 'PNG')  # Save the first page as PNG
    print(f"PDF converted to PNG: {output_png}")

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

    print(f"Range '{cell_range}' from sheet '{sheet_name}' has been printed to '{output_file}'.")


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

        print(f"Image saved successfully to: {output_image_path}")
        return output_image_path

    finally:
        # Clean up
        wb.close()
        app.quit()