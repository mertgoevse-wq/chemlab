"""
Compatibility layer for Python 3.10.
Provides backports of Python 3.11+ features.
"""

from datetime import datetime, timezone
from enum import Enum


# UTC timezone for Python < 3.11
UTC = timezone.utc


# StrEnum backport for Python < 3.11
class StrEnum(str, Enum):
    """Backport of StrEnum for Python < 3.11"""
    pass


# Self type hint backport for Python < 3.11
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self
