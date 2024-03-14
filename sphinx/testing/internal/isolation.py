"""Private module containing isolation-related objects and functionalities.

Use literal strings or booleans to indicate isolation policies instead of
directly using :class:`Isolation` objects, unless it is used internally.
"""

from __future__ import annotations

__all__ = ()

from enum import IntEnum
from enum import auto as _auto
from typing import Literal, Union


class Isolation(IntEnum):
    """Isolation policy for the testing application."""

    minimal = _auto()
    """Minimal isolation mode."""
    grouped = _auto()
    """Similar to :attr:`always` but for parametrized tests."""
    always = _auto()
    """Copy the original testroot to a unique sources and build directory."""


IsolationPolicy = Union[bool, Literal['minimal', 'grouped', 'always']]
"""Allowed values for the isolation policy."""

NormalizableIsolation = Union[IsolationPolicy, Isolation]
"""Normalizable isolation value."""


def normalize_isolation_policy(policy: NormalizableIsolation) -> Isolation:
    """Normalize isolation policy into a :class:`Isolation` object."""
    if isinstance(policy, Isolation):
        return policy

    if isinstance(policy, bool):
        return Isolation.always if policy else Isolation.minimal

    if isinstance(policy, str) and hasattr(Isolation, policy):
        return getattr(Isolation, policy)

    msg = f'unknown isolation policy: {policy!r}'
    raise TypeError(msg)
