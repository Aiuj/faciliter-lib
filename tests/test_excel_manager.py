"""Tests for ExcelManager functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

# Test imports
def test_excel_manager_import():
    """Test that ExcelManager can be imported from faciliter_lib.tools."""
    from faciliter_lib.tools import ExcelManager
    assert ExcelManager is not None


class TestExcelManager:
    """Test ExcelManager class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_excel_path = "/fake/path/test.xlsx"
        
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_excel_manager_init(self, mock_load_workbook):
        """Test ExcelManager initialization."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        assert manager.excel_path == self.test_excel_path
        assert manager.wb is None
        
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_load_workbook_success(self, mock_load_workbook):
        """Test successful workbook loading."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock the workbook
        mock_wb = Mock()
        mock_wb.sheetnames = ['Sheet1', 'Sheet2']
        mock_load_workbook.return_value = mock_wb
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.load()
        
        assert result == mock_wb
        assert manager.wb == mock_wb
        mock_load_workbook.assert_called_once_with(self.test_excel_path, read_only=True)
        
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_load_workbook_failure(self, mock_load_workbook):
        """Test workbook loading failure."""
        from faciliter_lib.tools import ExcelManager
        
        mock_load_workbook.side_effect = Exception("File not found")
        
        manager = ExcelManager(self.test_excel_path)
        
        with pytest.raises(Exception) as exc_info:
            manager.load()
        
        assert "File not found" in str(exc_info.value)
        assert manager.wb is None
        
    def test_clean_cell_none(self):
        """Test cleaning None cell values."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.clean_cell(None)
        assert result == ''
        
    def test_clean_cell_nan(self):
        """Test cleaning NaN cell values."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.clean_cell(float('nan'))
        assert result == ''
        
    def test_clean_cell_normal_value(self):
        """Test cleaning normal cell values."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.clean_cell("test value")
        assert result == "test value"
        
        result = manager.clean_cell(42)
        assert result == 42
        
    def test_get_sheet_tables_basic(self):
        """Test basic sheet table extraction."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock worksheet with basic data
        mock_ws = Mock()
        mock_ws.values = [
            ['Name', 'Age', 'City'],
            ['Alice', 25, 'New York'],
            ['Bob', 30, 'London']
        ]
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.get_sheet_tables(mock_ws)
        
        # Should have 3 rows (including header)
        assert len(result) == 3
        assert result[0] == ['Name', 'Age', 'City']
        assert result[1] == ['Alice', 25, 'New York']  # Fixed assertion
        assert result[2] == ['Bob', 30, 'London']
        
    def test_get_sheet_tables_with_headers(self):
        """Test sheet table extraction with Excel-style headers."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock worksheet
        mock_ws = Mock()
        mock_ws.values = [
            ['Data1', 'Data2'],
            ['Value1', 'Value2']
        ]
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.get_sheet_tables(mock_ws, add_col_headers=True, add_row_headers=True)
        
        # Should have column headers (A, B) and row numbers
        assert len(result) >= 2
        # First row should have column headers
        assert 'A' in result[0] and 'B' in result[0]
        
    def test_get_sheet_tables_max_rows(self):
        """Test sheet table extraction with row limit."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock worksheet with more data
        mock_ws = Mock()
        mock_ws.values = [
            ['Header1', 'Header2'],
            ['Row1Col1', 'Row1Col2'],
            ['Row2Col1', 'Row2Col2'],
            ['Row3Col1', 'Row3Col2']
        ]
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.get_sheet_tables(mock_ws, max_rows=2)
        
        # Should limit to 2 rows
        assert len(result) <= 2
        
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_get_content_not_loaded(self, mock_load_workbook):
        """Test get_content when workbook is not loaded."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        
        with pytest.raises(ValueError) as exc_info:
            manager.get_content()
        
        assert "Workbook not loaded" in str(exc_info.value)
        
    @patch('faciliter_lib.tools.excel_manager.tabulate')
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_get_content_success(self, mock_load_workbook, mock_tabulate):
        """Test successful content extraction."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock workbook and worksheet
        mock_wb = MagicMock()
        mock_wb.sheetnames = ['Sheet1']
        mock_ws = Mock()
        mock_ws.values = [
            ['Name', 'Age'],
            ['Alice', 25]
        ]
        mock_wb.__getitem__.return_value = mock_ws
        mock_load_workbook.return_value = mock_wb
        
        # Mock tabulate
        mock_tabulate.return_value = "| Name | Age |\n|------|-----|\n| Alice | 25 |"
        
        manager = ExcelManager(self.test_excel_path)
        manager.load()
        
        with patch('faciliter_lib.utils.language_utils.LanguageUtils.detect_language') as mock_detect:
            mock_detect.return_value = 'en'
            
            result = manager.get_content()
            
            assert len(result) == 1
            assert result[0]['sheet_name'] == 'Sheet1'
            assert 'markdown' in result[0]
            assert result[0]['language'] == 'en'
            assert 'rows' in result[0]
            
    @patch('faciliter_lib.tools.excel_manager.tabulate')
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_to_markdown_not_loaded(self, mock_load_workbook, mock_tabulate):
        """Test to_markdown when workbook is not loaded."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        
        with pytest.raises(ValueError) as exc_info:
            manager.to_markdown()
        
        assert "Workbook not loaded" in str(exc_info.value)
        
    @patch('faciliter_lib.tools.excel_manager.tabulate')
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_to_combined_markdown_not_loaded(self, mock_load_workbook, mock_tabulate):
        """Test to_combined_markdown when workbook is not loaded."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        
        with pytest.raises(ValueError) as exc_info:
            manager.to_combined_markdown()
        
        assert "Workbook not loaded" in str(exc_info.value)
        
    @patch('faciliter_lib.tools.excel_manager.tabulate')
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_to_markdown_success(self, mock_load_workbook, mock_tabulate):
        """Test successful markdown conversion."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock workbook with multiple sheets
        mock_wb = MagicMock()
        mock_wb.sheetnames = ['Sheet1', 'Sheet2']
        
        # Mock worksheets
        mock_ws1 = Mock()
        mock_ws1.values = [['Name', 'Age'], ['Alice', 25]]
        mock_ws2 = Mock()
        mock_ws2.values = [['Product', 'Price'], ['Apple', 1.50]]
        
        def mock_getitem(key):
            if key == 'Sheet1':
                return mock_ws1
            elif key == 'Sheet2':
                return mock_ws2
            
        mock_wb.__getitem__.side_effect = mock_getitem
        mock_load_workbook.return_value = mock_wb
        
        # Mock tabulate
        mock_tabulate.return_value = "| Header | Value |\n|--------|-------|\n| Data | 123 |"
        
        manager = ExcelManager(self.test_excel_path)
        manager.load()
        
        result = manager.to_markdown()
        
        # Should return a list of dictionaries
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Check first sheet
        assert result[0]['sheet_name'] == 'Sheet1'
        assert 'markdown' in result[0]
        assert 'language' in result[0]  # Language detection is enabled by default
        
        # Check second sheet
        assert result[1]['sheet_name'] == 'Sheet2'
        assert 'markdown' in result[1]
        assert 'language' in result[1]
        
        # Should call tabulate for each sheet
        assert mock_tabulate.call_count == 2
        
    @patch('faciliter_lib.tools.excel_manager.tabulate')
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_to_combined_markdown_success(self, mock_load_workbook, mock_tabulate):
        """Test successful combined markdown conversion."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock workbook with multiple sheets
        mock_wb = MagicMock()
        mock_wb.sheetnames = ['Sheet1', 'Sheet2']
        
        # Mock worksheets
        mock_ws1 = Mock()
        mock_ws1.values = [['Name', 'Age'], ['Alice', 25]]
        mock_ws2 = Mock()
        mock_ws2.values = [['Product', 'Price'], ['Apple', 1.50]]
        
        def mock_getitem(key):
            if key == 'Sheet1':
                return mock_ws1
            elif key == 'Sheet2':
                return mock_ws2
            
        mock_wb.__getitem__.side_effect = mock_getitem
        mock_load_workbook.return_value = mock_wb
        
        # Mock tabulate
        mock_tabulate.return_value = "| Header | Value |\n|--------|-------|\n| Data | 123 |"
        
        manager = ExcelManager(self.test_excel_path)
        manager.load()
        
        result = manager.to_combined_markdown()
        
        # Should return a single string with sheet headers
        assert isinstance(result, str)
        assert '## Sheet1' in result
        assert '## Sheet2' in result
        # Should call tabulate for each sheet
        assert mock_tabulate.call_count == 2
        
    def test_excel_col_name_generation(self):
        """Test Excel column name generation (A, B, ..., Z, AA, AB, ...)."""
        from faciliter_lib.tools import ExcelManager
        
        manager = ExcelManager(self.test_excel_path)
        
        # Test with mock worksheet to trigger column header generation
        mock_ws = Mock()
        mock_ws.values = [['Data']]
        
        result = manager.get_sheet_tables(mock_ws, add_col_headers=True)
        
        # Should have at least one column header
        assert len(result) >= 1
        # The first row should contain column headers when add_col_headers=True
        if result:
            # Check that we have some form of column identifier
            assert len(result[0]) >= 1
            
    @patch('faciliter_lib.tools.excel_manager.load_workbook')
    def test_get_content_no_language_detection(self, mock_load_workbook):
        """Test get_content with language detection disabled."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock workbook and worksheet
        mock_wb = MagicMock()
        mock_wb.sheetnames = ['Sheet1']
        mock_ws = Mock()
        mock_ws.values = [['Header'], ['Data']]
        mock_wb.__getitem__.return_value = mock_ws
        mock_load_workbook.return_value = mock_wb
        
        manager = ExcelManager(self.test_excel_path)
        manager.load()
        
        with patch('faciliter_lib.tools.excel_manager.tabulate') as mock_tabulate:
            mock_tabulate.return_value = "| Header |\n|--------|\n| Data |"
            
            result = manager.get_content(detect_language=False)
            
            assert len(result) == 1
            assert result[0]['language'] is None
            
    def test_empty_worksheet_handling(self):
        """Test handling of empty worksheets."""
        from faciliter_lib.tools import ExcelManager
        
        # Mock empty worksheet
        mock_ws = Mock()
        mock_ws.values = []
        
        manager = ExcelManager(self.test_excel_path)
        result = manager.get_sheet_tables(mock_ws)
        
        # Should handle empty data gracefully
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__])