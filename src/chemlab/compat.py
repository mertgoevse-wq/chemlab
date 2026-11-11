"""
Compatibility layer for Python 3.10.
Provides backports of Python 3.11+ features.
"""

from datetime import UTC
from enum import Enum

# UTC timezone for Python < 3.11
UTC = UTC


# StrEnum backport for Python < 3.11
class StrEnum(str, Enum):
    """Backport of StrEnum for Python < 3.11"""

    pass


# Self type hint backport for Python < 3.11
try:
    from typing import Self
except ImportError:
    pass
