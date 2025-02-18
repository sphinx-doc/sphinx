from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Sequence, Set
    from pathlib import Path
    from typing import Final

LOGGER: Final[logging.SphinxLoggerAdapter] = logging.getLogger('sphinx.ext.apidoc')


def _remove_old_files(
    written_files: Sequence[Path], dest_dir: Path, suffix: str
) -> None:
    files_to_keep = frozenset(written_files)
    for existing in dest_dir.rglob(f'*.{suffix}'):
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


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ApidocOptions:
    """Options for apidoc."""

    module_path: Path
    dest_dir: Path

    exclude_pattern: Sequence[str] = ()
    quiet: bool = False
    max_depth: int = 4
    force: bool = False
    follow_links: bool = False
    dry_run: bool = False
    separate_modules: bool = False
    include_private: bool = False
    toc_file: str = 'modules'
    no_headings: bool = False
    module_first: bool = False
    implicit_namespaces: bool = False
    automodule_options: Set[str] = dataclasses.field(default_factory=set)
    suffix: str = 'rst'

    remove_old: bool = False

    # --full only
    full: bool = False
    append_syspath: bool = False
    header: str = ''
    author: str | None = None
    version: str | None = None
    release: str | None = None
    extensions: Sequence[str] | None = None
    template_dir: str | None = None
