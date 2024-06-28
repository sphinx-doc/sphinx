"""Docutils utility functions for parsing text."""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes

if TYPE_CHECKING:
    from docutils.parsers.rst.states import Inliner, RSTState, Struct


def inliner_parse_text(
    text: str, *, state: RSTState, lineno: int = 1,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    """Parse *text* as inline nodes.

    The text cannot contain any structural elements (headings, transitions,
    directives, etc), so should be a simple line or paragraph of text.
    """
    inliner: Inliner = state.inliner
    memo: Struct = state.memo
    parent: nodes.Element = state.parent
    return inliner.parse(text, lineno, memo, parent)
