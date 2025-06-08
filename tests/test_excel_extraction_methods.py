"""
Test module for Excel extraction methods.

This module contains comprehensive tests for:
- extract_members_from_reserves_sheet
- extract_members_from_members_sheet
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List

# Import the functions and classes we want to test
from excel import extract_members_from_reserves_sheet, extract_members_from_members_sheet, SiegeExcelSheets
from siege.siege_planner import SiegeAssignment, Member


def create_mock_xlwings_setup(mock_data):
    """Helper function to create consistent xlwings mocking setup."""
    mock_app = Mock()
    mock_wb = Mock()
    mock_sheet = Mock()
    mock_range = Mock()
    mock_range.value = mock_data

    # Properly mock the sheets access: wb.sheets[sheet_name]
    mock_sheets = MagicMock()
    mock_sheets.__getitem__.return_value = mock_sheet
    mock_wb.sheets = mock_sheets
    
    mock_sheet.range.return_value = mock_range
    
    return mock_app, mock_wb, mock_sheet


class TestExtractMembersFromReservesSheet:
    """Test cases for extract_members_from_reserves_sheet function."""

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_valid_data(self, mock_xw):
        """Test successful extraction of valid siege assignment data."""
        # Mock Excel data
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],
            ["Bob", None, "", 2],
            ["Charlie", None, "X", 1],
            ["Diana", None, None, 2]
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)

        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        # Mock SiegeExcelSheets
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            # Execute function
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            # Assertions
            assert len(result) == 4
            
            # Check first member (Alice)
            assert result[0].name == "Alice"
            assert result[0].attack_day == 1
            assert result[0].set_reserve == True
            
            # Check second member (Bob)
            assert result[1].name == "Bob"
            assert result[1].attack_day == 2
            assert result[1].set_reserve == False
            
            # Check third member (Charlie)
            assert result[2].name == "Charlie"
            assert result[2].attack_day == 1
            assert result[2].set_reserve == True
            
            # Check fourth member (Diana)
            assert result[3].name == "Diana"
            assert result[3].attack_day == 2
            assert result[3].set_reserve == False

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_empty_rows(self, mock_xw):
        """Test handling of empty rows and missing data."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],
            [None, None, None, None],  # Empty row
            ["", "", "", ""],  # Row with empty strings
            ["Bob", None, "", 2],
            ["", None, "X", 1]  # Empty name
        ]
        
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            # Should only return valid entries (Alice and Bob)
            assert len(result) == 2
            assert result[0].name == "Alice"
            assert result[1].name == "Bob"

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_invalid_attack_day(self, mock_xw):
        """Test handling of invalid attack day values."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],  # Valid
            ["Bob", None, "", 3],    # Invalid attack day
            ["Charlie", None, "X", "invalid"],  # Non-numeric attack day
            ["Diana", None, "", None]  # Missing attack day
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            # Should only return valid entry (Alice)
            assert len(result) == 1
            assert result[0].name == "Alice"


    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_set_reserve_variations(self, mock_xw):
        """Test different variations of set_reserve values."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],      # Standard X
            ["Bob", None, "x", 2],        # Lowercase x
            ["Charlie", None, "YES", 1],  # Text without X
            ["Diana", None, "", 2],       # Empty string
            ["Eve", None, None, 1]        # None value
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            assert len(result) == 5
            assert result[0].set_reserve == True   # X
            assert result[1].set_reserve == True   # x (uppercase conversion)
            assert result[2].set_reserve == False  # YES (no X)
            assert result[3].set_reserve == False  # Empty string
            assert result[4].set_reserve == False  # None

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_insufficient_columns(self, mock_xw):
        """Test handling of rows with insufficient columns."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],  # Complete row
            ["Bob", None, "X"],       # Missing attack day column
            ["Charlie", None],        # Missing multiple columns
            ["Diana"]                 # Only name column
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            # Should only return complete row (Alice)
            assert len(result) == 1
            assert result[0].name == "Alice"

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_excel_error(self, mock_xw):
        """Test handling of Excel-related errors."""
        # Setup mock to raise an exception
        mock_app = Mock()
        mock_xw.App.return_value = mock_app
        mock_app.books.open.side_effect = Exception("Excel file not found")
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            with pytest.raises(Exception, match="Excel file not found"):
                extract_members_from_reserves_sheet("/root", "nonexistent_file.xlsx")


class TestExtractMembersFromMembersSheet:
    """Test cases for extract_members_from_members_sheet function."""

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_valid_data(self, mock_xw):
        """Test successful extraction of valid member data."""
        # Mock Excel data (columns A-E, focusing on A and E)
        mock_data = [
            ["Name", "Col_B", "Col_C", "Col_D", "PostRestrictions"],  # Header row
            ["Alice", "ignored", "ignored", "ignored", "Post1,Post2,Post3"],
            ["Bob", "ignored", "ignored", "ignored", "SinglePost"],
            ["Charlie", "ignored", "ignored", "ignored", ""],  # Empty restrictions
            ["Diana", "ignored", "ignored", "ignored", None]   # None restrictions
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        # Mock SiegeExcelSheets
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            # Execute function
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            # Assertions
            assert len(result) == 4
            
            # Check first member (Alice)
            assert result[0].name == "Alice"
            assert result[0].post_restriction == ["Post1", "Post2", "Post3"]
            assert result[0].siege_assignment is None
            
            # Check second member (Bob)
            assert result[1].name == "Bob"
            assert result[1].post_restriction == ["SinglePost"]
            assert result[1].siege_assignment is None
            
            # Check third member (Charlie)
            assert result[2].name == "Charlie"
            assert result[2].post_restriction is None
            assert result[2].siege_assignment is None
            
            # Check fourth member (Diana)
            assert result[3].name == "Diana"
            assert result[3].post_restriction is None
            assert result[3].siege_assignment is None

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_post_restriction_whitespace(self, mock_xw):
        """Test handling of whitespace in post restrictions."""
        mock_data = [
            ["Name", "Col_B", "Col_C", "Col_D", "PostRestrictions"],  # Header row
            ["Alice", "ignored", "ignored", "ignored", " Post1 , Post2 , Post3 "],
            ["Bob", "ignored", "ignored", "ignored", "Post1,,,Post2,"],  # Extra commas
            ["Charlie", "ignored", "ignored", "ignored", "  ,  ,  "],  # Only whitespace and commas
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            assert len(result) == 3
            
            # Check Alice (whitespace trimmed)
            assert result[0].name == "Alice"
            assert result[0].post_restriction == ["Post1", "Post2", "Post3"]
            
            # Check Bob (empty strings filtered out)
            assert result[1].name == "Bob"
            assert result[1].post_restriction == ["Post1", "Post2"]
            
            # Check Charlie (only whitespace becomes None)
            assert result[2].name == "Charlie"
            assert result[2].post_restriction is None

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_missing_columns(self, mock_xw):
        """Test handling of rows with missing columns."""
        mock_data = [
            ["Name", "Col_B", "Col_C", "Col_D", "PostRestrictions"],  # Header row
            ["Alice", "ignored", "ignored", "ignored", "Post1,Post2"],  # Complete row
            ["Bob", "ignored", "ignored", "ignored"],                   # Missing column E
            ["Charlie", "ignored", "ignored"],                          # Missing columns D and E
            ["Diana"]                                                    # Only name column
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            # All members should be extracted, but those without column E should have None post_restriction
            assert len(result) == 4
            
            assert result[0].name == "Alice"
            assert result[0].post_restriction == ["Post1", "Post2"]
            
            assert result[1].name == "Bob"
            assert result[1].post_restriction is None
            
            assert result[2].name == "Charlie"
            assert result[2].post_restriction is None
            
            assert result[3].name == "Diana"
            assert result[3].post_restriction is None

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_empty_names(self, mock_xw):
        """Test handling of empty or None member names."""
        mock_data = [
            ["Name", "Col_B", "Col_C", "Col_D", "PostRestrictions"],  # Header row
            ["Alice", "ignored", "ignored", "ignored", "Post1"],
            [None, "ignored", "ignored", "ignored", "Post2"],      # None name
            ["", "ignored", "ignored", "ignored", "Post3"],        # Empty string name
            ["  ", "ignored", "ignored", "ignored", "Post4"],      # Whitespace only name
            ["Bob", "ignored", "ignored", "ignored", "Post5"]
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            # Should only return valid names (Alice and Bob)
            assert len(result) == 2
            assert result[0].name == "Alice"
            assert result[1].name == "Bob"

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_member_creation_error(self, mock_xw):
        """Test handling of errors during Member object creation."""
        mock_data = [
            ["Name", "Col_B", "Col_C", "Col_D", "PostRestrictions"],  # Header row
            ["ValidMember", "ignored", "ignored", "ignored", "Post1"],
            ["InvalidMember", "ignored", "ignored", "ignored", "Post2"]
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            # Mock Member constructor to raise exception for specific name
            with patch('excel.Member') as mock_member_class:
                def side_effect(*args, **kwargs):
                    if kwargs.get('name') == 'InvalidMember':
                        raise ValueError("Simulated validation error")
                    return Member(*args, **kwargs)
                
                mock_member_class.side_effect = side_effect
                
                
                result = extract_members_from_members_sheet("/root", "test_file.xlsx")
                
                # Should only return valid member
                assert len(result) == 1
                assert result[0].name == "ValidMember"


    @patch('excel.xw')
    def test_extract_members_from_members_sheet_excel_cleanup(self, mock_xw):
        """Test that Excel application is properly cleaned up."""
        mock_data = [
            ["Name", "Col_B", "Col_C", "Col_D", "PostRestrictions"],  # Header row
            ["Alice", "ignored", "ignored", "ignored", "Post1"]
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            # Verify cleanup was called
            mock_wb.close.assert_called_once()
            mock_app.quit.assert_called_once()

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_empty_data(self, mock_xw):
        """Test handling of completely empty data."""
        mock_data = [
            ["Name", "Col_B", "Col_C", "Col_D", "PostRestrictions"]  # Only header row
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            # Should return empty list
            assert len(result) == 0