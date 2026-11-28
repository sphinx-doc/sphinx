from typing import TypedDict

BOXES = 2
"""Boxes in a crate."""


class _Fields(TypedDict, total=False):
    weight: int
    """How heavy the crate is."""


class Crate(_Fields, total=False):
    """A crate of fruits."""

    color: str
    """The color of the crate."""
