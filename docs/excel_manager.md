# ExcelManager Documentation

The `ExcelManager` class provides a simple interface for loading, reading, and converting Excel files to markdown format. It supports reading multiple sheets, extracting data as tables, and generating markdown output with optional language detection.

## Installation

The `ExcelManager` is part of the core-lib package and comes with the required dependencies:

```bash
pip install core-lib
```

The following dependencies are automatically installed:
- `openpyxl>=3.1.5` - For reading Excel files
- `tabulate>=0.9.0` - For generating markdown tables

## Basic Usage

### Import

```python
# Import from the main package
from core_lib import ExcelManager

# Or import from the tools submodule
from core_lib.tools import ExcelManager
```

### Loading and Converting Excel Files

```python
from core_lib import ExcelManager

# Initialize with path to Excel file
excel_manager = ExcelManager("path/to/your/file.xlsx")

# Load the workbook
workbook = excel_manager.load()

# Convert all sheets to individual markdown tables (NEW API)
sheet_markdowns = excel_manager.to_markdown()

# Each item in the list has sheet info and markdown
for sheet_data in sheet_markdowns:
    print(f"Sheet: {sheet_data['sheet_name']}")
    print(f"Language: {sheet_data['language']}")
    print(sheet_data['markdown'])
    print("---")

# Or get combined markdown with titles (NEW METHOD)
combined_markdown = excel_manager.to_combined_markdown()
print(combined_markdown)
```

### Getting Structured Content

```python
from core_lib import ExcelManager

excel_manager = ExcelManager("data.xlsx")
excel_manager.load()

# Get structured content with metadata
content = excel_manager.get_content()

for sheet_data in content:
    print(f"Sheet: {sheet_data['sheet_name']}")
    print(f"Language: {sheet_data['language']}")
    print(f"Rows: {len(sheet_data['rows'])}")
    print(sheet_data['markdown'])
    print("---")
```

## Advanced Options

### Limiting Row Output

```python
# Limit to first 10 rows per sheet
sheet_markdowns = excel_manager.to_markdown(max_rows=10)

# Or for combined markdown
combined_markdown = excel_manager.to_combined_markdown(max_rows=10)

# Or for structured content
content = excel_manager.get_content(max_rows=10)
```

### Excel-Style Headers

```python
# Add column headers (A, B, C, ...) and row numbers (1, 2, 3, ...)
sheet_markdowns = excel_manager.to_markdown(
    add_col_headers=True,   # Adds A, B, C column headers
    add_row_headers=True    # Adds 1, 2, 3 row numbers
)

# Disable headers for cleaner output
sheet_markdowns = excel_manager.to_markdown(
    add_col_headers=False,
    add_row_headers=False
)

# Same options work for combined markdown
combined_markdown = excel_manager.to_combined_markdown(
    add_col_headers=True,
    add_row_headers=True
)
```

### Language Detection

```python
# Enable automatic language detection (default)
sheet_markdowns = excel_manager.to_markdown(detect_language=True)
for sheet_data in sheet_markdowns:
    print(f"Sheet {sheet_data['sheet_name']} language: {sheet_data['language']}")

# Disable language detection for faster processing
sheet_markdowns = excel_manager.to_markdown(detect_language=False)
# language will be None for all sheets

# Same options work for combined markdown and get_content
content = excel_manager.get_content(detect_language=False)
```

## Complete Example

```python
from core_lib import ExcelManager
import os

def process_excel_file(file_path):
    """Process an Excel file and return markdown content with metadata."""
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    try:
        # Initialize and load
        manager = ExcelManager(file_path)
        workbook = manager.load()
        
        print(f"Loaded workbook with sheets: {workbook.sheetnames}")
        
        # Get individual sheet markdowns (NEW API)
        sheet_markdowns = manager.to_markdown(
            max_rows=100,           # Limit to 100 rows per sheet
            add_col_headers=True,   # Include A, B, C headers
            add_row_headers=True,   # Include 1, 2, 3 row numbers
            detect_language=True    # Detect content language
        )
        
        # Process each sheet individually
        for sheet_data in sheet_markdowns:
            print(f"Sheet '{sheet_data['sheet_name']}': "
                  f"language: {sheet_data['language']}")
        
        # Or get combined markdown with titles
        combined_markdown = manager.to_combined_markdown(
            max_rows=100,
            add_col_headers=True,
            add_row_headers=True,
            detect_language=True
        )
        
        # Get structured content with metadata (alternative approach)
        content = manager.get_content(
            max_rows=100,           # Limit to 100 rows per sheet
            add_col_headers=True,   # Include A, B, C headers
            add_row_headers=True,   # Include 1, 2, 3 row numbers
            detect_language=True    # Detect content language
        )
        
        # Process each sheet
        results = []
        for sheet_data in content:
            sheet_info = {
                'name': sheet_data['sheet_name'],
                'language': sheet_data['language'],
                'row_count': len(sheet_data['rows']),
                'markdown': sheet_data['markdown']
            }
            results.append(sheet_info)
            
            # Print summary
            print(f"Sheet '{sheet_info['name']}': "
                  f"{sheet_info['row_count']} rows, "
                  f"language: {sheet_info['language']}")
        
        return results, sheet_markdowns, combined_markdown
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        raise

# Usage
if __name__ == "__main__":
    try:
        results, sheet_markdowns, combined_markdown = process_excel_file("sample_data.xlsx")
        
        # Save individual sheet markdowns
        for i, sheet_data in enumerate(sheet_markdowns):
            filename = f"sheet_{i+1}_{sheet_data['sheet_name']}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# {sheet_data['sheet_name']}\n\n")
                f.write(f"**Language:** {sheet_data['language']}\n\n")
                f.write(sheet_data['markdown'])
            print(f"Sheet markdown saved to {filename}")
        
        # Save combined markdown
        with open("combined_output.md", "w", encoding="utf-8") as f:
            f.write("# Excel Workbook Contents\n\n")
            f.write(combined_markdown)
        print("Combined markdown saved to combined_output.md")
        
        # Save structured output (alternative)
        with open("structured_output.md", "w", encoding="utf-8") as f:
            for result in results:
                f.write(f"# {result['name']}\n\n")
                f.write(f"**Language:** {result['language']}\n")
                f.write(f"**Rows:** {result['row_count']}\n\n")
                f.write(result['markdown'])
                f.write("\n\n---\n\n")
        print("Structured output saved to structured_output.md")
        
    except Exception as e:
        print(f"Failed to process file: {e}")
```

## Error Handling

The `ExcelManager` provides clear error messages for common issues:

```python
from core_lib import ExcelManager

manager = ExcelManager("nonexistent.xlsx")

try:
    manager.load()
except FileNotFoundError:
    print("Excel file not found")
except Exception as e:
    print(f"Error loading Excel file: {e}")

# Trying to get content before loading
try:
    content = manager.get_content()  # Will raise ValueError
except ValueError as e:
    print(f"Error: {e}")  # "Workbook not loaded. Call load() first."
```

## Method Reference

### `__init__(excel_path)`
Initialize the ExcelManager with the path to an Excel file.

**Parameters:**
- `excel_path` (str): Path to the Excel file

### `load()`
Load the Excel workbook from the specified path.

**Returns:**
- `Workbook`: The loaded openpyxl Workbook object

**Raises:**
- `Exception`: If the file cannot be loaded

### `get_content(max_rows=None, add_col_headers=True, add_row_headers=True, detect_language=True)`
Extract content from all sheets with metadata.

**Parameters:**
- `max_rows` (int, optional): Maximum number of rows per sheet
- `add_col_headers` (bool): Add Excel-style column headers (A, B, C, ...)
- `add_row_headers` (bool): Add Excel-style row numbers (1, 2, 3, ...)
- `detect_language` (bool): Enable automatic language detection

**Returns:**
- `list`: List of dictionaries with keys:
  - `sheet_name`: Name of the sheet
  - `markdown`: Markdown table content
  - `language`: Detected language (if enabled)
  - `rows`: Raw row data

### `to_markdown(max_rows=None, add_col_headers=True, add_row_headers=True, detect_language=True)`
Convert all sheets to individual markdown tables.

**Parameters:**
- `max_rows` (int, optional): Maximum number of rows per sheet
- `add_col_headers` (bool): Add Excel-style column headers (A, B, C, ...)
- `add_row_headers` (bool): Add Excel-style row numbers (1, 2, 3, ...)
- `detect_language` (bool): Enable automatic language detection

**Returns:**
- `list`: List of dictionaries with keys:
  - `sheet_name`: Name of the sheet/tab
  - `markdown`: Markdown table content
  - `language`: Detected language (if enabled)

### `to_combined_markdown(max_rows=None, add_col_headers=True, add_row_headers=True, detect_language=True)`
Convert all sheets to a single combined markdown string with titles per tab.

**Parameters:**
- Same as `to_markdown()`

**Returns:**
- `str`: Combined markdown-formatted string with all sheets, each with its own title

### `get_sheet_tables(ws, max_rows=None, add_col_headers=False, add_row_headers=False)`
Extract data from a single worksheet.

**Parameters:**
- `ws`: Worksheet object
- `max_rows` (int, optional): Maximum number of rows
- `add_col_headers` (bool): Add column headers
- `add_row_headers` (bool): Add row headers

**Returns:**
- `list`: Sheet data as list of lists

### `clean_cell(cell)`
Clean cell values (convert None and NaN to empty strings).

**Parameters:**
- `cell`: Cell value to clean

**Returns:**
- Cleaned cell value

## Dependencies

The ExcelManager requires these packages which are automatically installed:

- **openpyxl**: For reading Excel files (.xlsx format)
- **tabulate**: For generating markdown tables
- **core_lib.utils.language_utils**: For language detection (when enabled)

## Notes

- Only supports `.xlsx` files (Excel 2007+ format)
- Files are loaded in read-only mode for performance
- Empty rows and columns are automatically filtered out
- Language detection uses the `LanguageUtils` class from core-lib
- All cell content is converted to strings in the output
- Large files are handled efficiently with streaming reads