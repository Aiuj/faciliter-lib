"""faciliter_lib.utils - Utility functions and classes.

This package provides utility functionality for the faciliter_lib library including:
- AppSettings: Application configuration and settings management
- LanguageUtils: Language detection, text manipulation, and NLP utilities
- File utilities: Temporary file creation and cleanup helpers

Convenience imports for the `faciliter_lib.utils` package.

Exports a small, stable surface so consumers can do::

    from faciliter_lib.utils import AppSettings, LanguageUtils
    from faciliter_lib.utils import create_tempfile, remove_tempfile

The package intentionally re-exports only the primary utilities implemented
in the package to keep the public API small and predictable.
"""

from .app_settings import AppSettings
from .language_utils import LanguageUtils
from .file_utils import create_tempfile, remove_tempfile

__all__ = ["AppSettings", "LanguageUtils", "create_tempfile", "remove_tempfile"]
