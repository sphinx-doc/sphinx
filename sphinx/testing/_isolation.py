from __future__ import annotations

__all__ = ['Isolation', 'IsolationPolicy', 'parse_isolation']

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


IsolationPolicy = Union[bool, Literal["minimal", "grouped", "always"], Isolation]


def parse_isolation(policy: IsolationPolicy | None) -> Isolation:
    if isinstance(policy, Isolation):
        return policy

    if policy is None:
        return Isolation.minimal

    if isinstance(policy, bool):
        return Isolation.always if policy else Isolation.minimal

    if isinstance(policy, str) and hasattr(Isolation, policy):
        return getattr(Isolation, policy)

    msg = f'unknown isolation policy: {policy!r}'
    raise TypeError(msg)
