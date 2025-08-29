"""Configuration helpers for faciliter_lib.

Expose category constants so applications can import them as
`from faciliter_lib import CATEGORIES` or `from faciliter_lib.config import CATEGORIES`.
"""
from .categories import DOC_CATEGORIES, CATEGORIES_BY_KEY, CATEGORY_CHOICES

__all__ = ["DOC_CATEGORIES", "CATEGORIES_BY_KEY", "CATEGORY_CHOICES"]
