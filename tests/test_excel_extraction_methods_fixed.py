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
    mock_sheets = Mock()
    mock_sheets.__getitem__ = Mock(return_value=mock_sheet)
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
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            # Should only extract Alice and Bob (valid entries)
            assert len(result) == 2
            assert result[0].name == "Alice"
            assert result[1].name == "Bob"

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_invalid_attack_days(self, mock_xw):
        """Test handling of invalid attack day values."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],  # Valid
            ["Bob", None, "", 3],     # Invalid attack day
            ["Charlie", None, "X", "invalid"],  # Invalid attack day
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
            
            # Should only extract Alice (only valid entry)
            assert len(result) == 1
            assert result[0].name == "Alice"
            assert result[0].attack_day == 1

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_set_reserve_variations(self, mock_xw):
        """Test various set reserve indicator formats."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],     # Standard X
            ["Bob", None, "x", 2],       # Lowercase x
            ["Charlie", None, "XX", 1],  # Multiple X
            ["Diana", None, "", 2],      # Empty string
            ["Eve", None, "Y", 1],       # Other character (should be False)
            ["Frank", None, None, 2]     # None value
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            assert len(result) == 6
            assert result[0].set_reserve == True   # Alice: "X"
            assert result[1].set_reserve == True   # Bob: "x"
            assert result[2].set_reserve == True   # Charlie: "XX"
            assert result[3].set_reserve == False  # Diana: ""
            assert result[4].set_reserve == False  # Eve: "Y"
            assert result[5].set_reserve == False  # Frank: None

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_insufficient_columns(self, mock_xw):
        """Test handling of rows with insufficient column data."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],  # Complete row
            ["Bob", None],            # Missing columns
            ["Charlie"]               # Only name
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            # Should only extract Alice (only complete row)
            assert len(result) == 1
            assert result[0].name == "Alice"

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_exception_handling(self, mock_xw):
        """Test exception handling during data processing."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],  # Header row
            ["Alice", None, "X", 1],  # Valid data
            ["Bob", None, "X", 2.0]   # Float attack day (should convert)
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            assert len(result) == 2
            assert result[0].name == "Alice"
            assert result[0].attack_day == 1
            assert result[1].name == "Bob"
            assert result[1].attack_day == 2  # Should convert from 2.0

    @patch('excel.xw')
    def test_extract_members_from_reserves_sheet_cleanup(self, mock_xw):
        """Test proper cleanup of Excel resources."""
        mock_data = [
            ["Name", "Unused", "SetReserve", "AttackDay"],
            ["Alice", None, "X", 1]
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'reserves_sheet') as mock_reserves_sheet:
            mock_reserves_sheet.name = "Reserves"
            mock_reserves_sheet.cell_range = "A1:D30"
            
            result = extract_members_from_reserves_sheet("/root", "test_file.xlsx")
            
            # Verify cleanup methods were called
            mock_wb.close.assert_called_once()
            mock_app.quit.assert_called_once()


class TestExtractMembersFromMembersSheet:
    """Test cases for extract_members_from_members_sheet function."""

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_valid_data(self, mock_xw):
        """Test successful extraction of valid member data."""
        mock_data = [
            ["Name", "Col2", "Col3", "Col4", "PostRestrictions"],  # Header row
            ["Alice", "data", "data", "data", "Post1, Post2"],
            ["Bob", "data", "data", "data", ""],
            ["Charlie", "data", "data", "data", "Post3"],
            ["Diana", "data", "data", "data", None]
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            assert len(result) == 4
            
            # Check Alice (multiple post restrictions)
            assert result[0].name == "Alice"
            assert result[0].post_restriction == ["Post1", "Post2"]
            
            # Check Bob (empty post restrictions)
            assert result[1].name == "Bob"
            assert result[1].post_restriction is None
            
            # Check Charlie (single post restriction)
            assert result[2].name == "Charlie"
            assert result[2].post_restriction == ["Post3"]
            
            # Check Diana (None post restrictions)
            assert result[3].name == "Diana"
            assert result[3].post_restriction is None

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_empty_rows(self, mock_xw):
        """Test handling of empty rows and missing names."""
        mock_data = [
            ["Name", "Col2", "Col3", "Col4", "PostRestrictions"],  # Header row
            ["Alice", "data", "data", "data", "Post1"],
            [None, None, None, None, None],  # Empty row
            ["", "", "", "", ""],            # Row with empty strings
            ["Bob", "data", "data", "data", "Post2"],
            ["", "data", "data", "data", "Post3"]  # Empty name
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            # Should only extract Alice and Bob (valid entries)
            assert len(result) == 2
            assert result[0].name == "Alice"
            assert result[1].name == "Bob"

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_post_restriction_parsing(self, mock_xw):
        """Test various post restriction formats."""
        mock_data = [
            ["Name", "Col2", "Col3", "Col4", "PostRestrictions"],  # Header row
            ["Alice", "data", "data", "data", "Post1,Post2,Post3"],     # No spaces
            ["Bob", "data", "data", "data", "Post1, Post2, Post3"],     # With spaces
            ["Charlie", "data", "data", "data", " Post1 , Post2 "],     # Extra spaces
            ["Diana", "data", "data", "data", "Post1,,Post3"],          # Empty item
            ["Eve", "data", "data", "data", ",Post1,"],                 # Leading/trailing commas
            ["Frank", "data", "data", "data", "   "],                   # Only whitespace
            ["Grace", "data", "data", "data", ",,,"]                    # Only commas
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            assert len(result) == 7
            assert result[0].post_restriction == ["Post1", "Post2", "Post3"]  # Alice
            assert result[1].post_restriction == ["Post1", "Post2", "Post3"]  # Bob
            assert result[2].post_restriction == ["Post1", "Post2"]           # Charlie
            assert result[3].post_restriction == ["Post1", "Post3"]           # Diana
            assert result[4].post_restriction == ["Post1"]                    # Eve
            assert result[5].post_restriction is None                         # Frank
            assert result[6].post_restriction is None                         # Grace

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_insufficient_columns(self, mock_xw):
        """Test handling of rows with insufficient column data."""
        mock_data = [
            ["Name", "Col2", "Col3", "Col4", "PostRestrictions"],  # Header row
            ["Alice", "data", "data", "data", "Post1"],  # Complete row
            ["Bob", "data", "data", "data"],             # Missing PostRestrictions column
            ["Charlie", "data"]                          # Very short row
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
            assert result[0].name == "Alice"
            assert result[0].post_restriction == ["Post1"]
            assert result[1].name == "Bob"
            assert result[1].post_restriction is None    # Missing column
            assert result[2].name == "Charlie"
            assert result[2].post_restriction is None    # Missing column

    @patch('excel.xw')
    def test_extract_members_from_members_sheet_cleanup(self, mock_xw):
        """Test proper cleanup of Excel resources."""
        mock_data = [
            ["Name", "Col2", "Col3", "Col4", "PostRestrictions"],
            ["Alice", "data", "data", "data", "Post1"]
        ]
        
        # Setup mocks
        mock_app, mock_wb, mock_sheet = create_mock_xlwings_setup(mock_data)
        mock_xw.App.return_value = mock_app
        mock_app.books.open.return_value = mock_wb
        
        with patch.object(SiegeExcelSheets, 'members_sheet') as mock_members_sheet:
            mock_members_sheet.name = "Members"
            mock_members_sheet.cell_range = "A1:E30"
            
            result = extract_members_from_members_sheet("/root", "test_file.xlsx")
            
            # Verify cleanup methods were called
            mock_wb.close.assert_called_once()
            mock_app.quit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
