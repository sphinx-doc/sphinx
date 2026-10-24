from __future__ import annotations

from target import _alias_impl

TokenValidator = _alias_impl.TokenValidator


def validate(value: _alias_impl.TokenValidator) -> None:
    """Validate a token."""
