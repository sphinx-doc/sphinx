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

from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

logger = logging.getLogger(__name__)


def _remove_old_files(
    written_files: Sequence[Path], destdir: Path, suffix: str
) -> None:
    files_to_keep = frozenset(written_files)
    for existing in destdir.rglob(f'*.{suffix}'):
        if existing not in files_to_keep:
            try:
                existing.unlink()
            except OSError as exc:
                logger.warning(
                    __('Failed to remove %s: %s'),
                    existing,
                    exc.strerror,
                    type='autodoc',
                )
