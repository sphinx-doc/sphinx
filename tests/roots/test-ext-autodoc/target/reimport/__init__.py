from typing import TypeVar

from ._private import T
from ._usage import add

V = TypeVar('V')
"""A locally defined TypeVar"""

__all__ = ['T', 'V', 'add']
