"""Some useful event listener factories for autodoc-process-docstring."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, Literal, TypeAlias

    from sphinx.application import Sphinx

    _AutodocObjType = Literal[
        'module', 'class', 'exception', 'function', 'method', 'attribute'
    ]
    _AutodocProcessDocstringListener: TypeAlias = Callable[
        [Sphinx, _AutodocObjType, str, Any, dict[str, bool], list[str]], None
    ]


def cut_lines(
    pre: int, post: int = 0, what: Sequence[str] | None = None
) -> _AutodocProcessDocstringListener:
    """Return a listener that removes the first *pre* and last *post*
    lines of every docstring.  If *what* is a sequence of strings,
    only docstrings of a type in *what* will be processed.

    Use like this (e.g. in the ``setup()`` function of :file:`conf.py`)::

       from sphinx.ext.autodoc import cut_lines

       app.connect('autodoc-process-docstring', cut_lines(4, what={'module'}))

    This can (and should) be used in place of :confval:`automodule_skip_lines`.
    """
    if not what:
        what_unique: frozenset[str] = frozenset()
    elif isinstance(what, str):  # strongly discouraged
        what_unique = frozenset({what})
    else:
        what_unique = frozenset(what)

    def process(
        app: Sphinx,
        what_: _AutodocObjType,
        name: str,
        obj: Any,
        options: dict[str, bool],
        lines: list[str],
    ) -> None:
        if what_unique and what_ not in what_unique:
            return
        del lines[:pre]
        if post:
            # remove one trailing blank line.
            if lines and not lines[-1]:
                lines.pop(-1)
            del lines[-post:]
        # make sure there is a blank line at the end
        if lines and lines[-1]:
            lines.append('')

    return process


def between(
    marker: str,
    what: Sequence[str] | None = None,
    keepempty: bool = False,
    exclude: bool = False,
) -> _AutodocProcessDocstringListener:
    """Return a listener that either keeps, or if *exclude* is True excludes,
    lines between lines that match the *marker* regular expression.  If no line
    matches, the resulting docstring would be empty, so no change will be made
    unless *keepempty* is true.

    If *what* is a sequence of strings, only docstrings of a type in *what* will
    be processed.
    """
    marker_re = re.compile(marker)

    def process(
        app: Sphinx,
        what_: _AutodocObjType,
        name: str,
        obj: Any,
        options: dict[str, bool],
        lines: list[str],
    ) -> None:
        if what and what_ not in what:
            return
        deleted = 0
        delete = not exclude
        orig_lines = lines.copy()
        for i, line in enumerate(orig_lines):
            if delete:
                lines.pop(i - deleted)
                deleted += 1
            if marker_re.match(line):
                delete = not delete
                if delete:
                    lines.pop(i - deleted)
                    deleted += 1
        if not lines and not keepempty:
            lines[:] = orig_lines
        # make sure there is a blank line at the end
        if lines and lines[-1]:
            lines.append('')

    return process
