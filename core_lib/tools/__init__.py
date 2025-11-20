"""Tools package for core_lib.

Expose utility classes so applications can import them from
`core_lib.tools` (e.g. `from core_lib.tools import ExcelManager`).
"""
from .excel_manager import ExcelManager  # re-export

__all__ = ["ExcelManager"]
