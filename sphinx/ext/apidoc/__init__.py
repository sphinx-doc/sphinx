"""Creates reST files corresponding to Python modules for code documentation.

Parses a directory tree looking for Python modules and packages and creates
ReST files appropriately to create code documentation with Sphinx.  It also
creates a modules index (named modules.<suffix>).

This is derived from the "sphinx-autopackage" script, which is:
Copyright 2008 Société des arts technologiques (SAT),
https://sat.qc.ca/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.ext.apidoc._cli import main

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: Sequence[str] = ('main',)
