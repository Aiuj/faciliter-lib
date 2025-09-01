"""Configuration helpers for faciliter_lib.

Expose category constants so applications can import them as
`from faciliter_lib import DOC_CATEGORIES` or `from faciliter_lib.config import DOC_CATEGORIES`.
"""
from .categories import DOC_CATEGORIES, DOC_CATEGORIES_BY_KEY, DOC_CATEGORY_CHOICES

__all__ = ["DOC_CATEGORIES", "DOC_CATEGORIES_BY_KEY", "DOC_CATEGORY_CHOICES"]
