from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Sequence, Set
    from pathlib import Path
    from typing import Final, Self

    from sphinx.config import Config

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


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ApidocOptions:
    """Options for apidoc."""

    destdir: Path
    module_path: Path

    exclude_pattern: Sequence[str] = ()
    maxdepth: int = 4
    followlinks: bool = False
    separatemodules: bool = False
    includeprivate: bool = False
    tocfile: str = 'modules'
    noheadings: bool = False
    modulefirst: bool = False
    implicit_namespaces: bool = False
    automodule_options: Set[str] = dataclasses.field(default_factory=set)
    suffix: str = 'rst'

    remove_old: bool = True

    quiet: bool = False
    dryrun: bool = False
    force: bool = True

    # --full only
    full: bool = False
    append_syspath: bool = False
    header: str = ''
    author: str | None = None
    version: str | None = None
    release: str | None = None
    extensions: Sequence[str] | None = None
    templatedir: str | None = None


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ApidocDefaults:
    """Default values for apidoc options."""

    exclude_patterns: list[str]
    automodule_options: frozenset[str]
    maxdepth: int
    followlinks: bool
    separatemodules: bool
    includeprivate: bool
    noheadings: bool
    modulefirst: bool
    implicit_namespaces: bool

    @classmethod
    def from_config(cls, config: Config, /) -> Self:
        """Collect the default values for apidoc options."""
        return cls(
            exclude_patterns=config.apidoc_exclude_patterns,
            automodule_options=frozenset(config.apidoc_automodule_options),
            maxdepth=config.apidoc_maxdepth,
            followlinks=config.apidoc_followlinks,
            separatemodules=config.apidoc_separatemodules,
            includeprivate=config.apidoc_includeprivate,
            noheadings=config.apidoc_noheadings,
            modulefirst=config.apidoc_modulefirst,
            implicit_namespaces=config.apidoc_implicit_namespaces,
        )
