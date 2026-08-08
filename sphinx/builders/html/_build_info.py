"""Record metadata for the build process."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.locale import __
from sphinx.util._serialise import stable_hash

if TYPE_CHECKING:
    from collections.abc import Set
    from pathlib import Path

    from sphinx.config import Config, _ConfigRebuild
    from sphinx.theming import Theme
    from sphinx.util.tags import Tags


class BuildInfo:
    """buildinfo file manipulator.

    HTMLBuilder and its family are storing their own envdata to ``.buildinfo``.
    This class is a manipulator for the file.
    """

    @classmethod
    def load(cls: type[BuildInfo], filename: Path, /) -> BuildInfo:
        content = filename.read_text(encoding='utf-8')
        lines = content.splitlines()

        version = lines[0].rstrip()
        if version != '# Sphinx build info version 1':
            msg = __('failed to read broken build info file (unknown version)')
            raise ValueError(msg)

        if not lines[2].startswith('config: '):
            msg = __('failed to read broken build info file (missing config entry)')
            raise ValueError(msg)
        if not lines[3].startswith('tags: '):
            msg = __('failed to read broken build info file (missing tags entry)')
            raise ValueError(msg)

        build_info = BuildInfo()
        build_info.config_hash = lines[2].removeprefix('config: ').strip()
        build_info.tags_hash = lines[3].removeprefix('tags: ').strip()
        # theme_hash is optional for backward compatibility
        # with old .buildinfo files that don't have it
        if len(lines) > 4 and lines[4].startswith('theme: '):
            build_info.theme_hash = lines[4].removeprefix('theme: ').strip()
        return build_info

    def __init__(
        self,
        config: Config | None = None,
        tags: Tags | None = None,
        config_categories: Set[_ConfigRebuild] = frozenset(),
        theme: Theme | None = None,
    ) -> None:
        self.config_hash = ''
        self.tags_hash = ''
        self.theme_hash = ''

        if config:
            values = {c.name: c.value for c in config.filter(config_categories)}
            self.config_hash = stable_hash(values)

        if tags:
            self.tags_hash = stable_hash(sorted(tags))

        if theme:
            # Hash all files in all theme dirs to detect any changes
            theme_files = {}
            for theme_dir in theme._dirs:
                for path in sorted(theme_dir.rglob('*')):
                    if path.is_file():
                        theme_files[str(path)] = path.read_bytes()
            self.theme_hash = stable_hash(theme_files)

    def __eq__(self, other: BuildInfo) -> bool:  # type: ignore[override]
        return (
            self.config_hash == other.config_hash
            and self.tags_hash == other.tags_hash
            and self.theme_hash == other.theme_hash
        )

    def __hash__(self) -> int:
        return hash((self.config_hash, self.tags_hash, self.theme_hash))

    def dump(self, filename: Path, /) -> None:
        build_info = (
            '# Sphinx build info version 1\n'
            '# This file records the configuration used when building these files. '
            'When it is not found, a full rebuild will be done.\n'
            f'config: {self.config_hash}\n'
            f'tags: {self.tags_hash}\n'
            f'theme: {self.theme_hash}\n'
        )
        filename.write_text(build_info, encoding='utf-8')
