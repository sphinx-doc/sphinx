from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Final

LOGGER: Final[logging.SphinxLoggerAdapter] = logging.getLogger('sphinx.ext.apidoc')


def _remove_old_files(
    written_files: Sequence[Path], destdir: Path, suffix: str
) -> None:
    files_to_keep = frozenset(written_files)
    for existing in destdir.rglob(f'*.{suffix}'):
        if existing not in files_to_keep:
            try:
                existing.unlink()
            except OSError as exc:
                LOGGER.warning(
                    __('Failed to remove %s: %s'),
                    existing,
                    exc.strerror,
                    type='autodoc',
                )
