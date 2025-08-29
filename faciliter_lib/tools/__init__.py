"""Tools package for faciliter_lib.

Expose utility classes so applications can import them from
`faciliter_lib.tools` (e.g. `from faciliter_lib.tools import ExcelManager`).
"""
from .excel_manager import ExcelManager  # re-export

__all__ = ["ExcelManager"]
