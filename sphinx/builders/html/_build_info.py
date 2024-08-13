"""Record metadata for the build process."""

from __future__ import annotations

import json
import types
from typing import TYPE_CHECKING

from sphinx.locale import __

if TYPE_CHECKING:
    from collections.abc import Set
    from pathlib import Path
    from typing import Any

    from sphinx.config import Config, _ConfigRebuild
    from sphinx.util.tags import Tags


class BuildInfo:
    """buildinfo file manipulator.

    HTMLBuilder and its family are storing their own envdata to ``.buildinfo``.
    This class is a manipulator for the file.
    """

    @classmethod
    def load(cls: type[BuildInfo], filename: Path, /) -> BuildInfo:
        content = filename.read_text(encoding="utf-8")
        lines = content.splitlines()

        version = lines[0].rstrip()
        if version == '# Sphinx build info version 1':
            return BuildInfo()  # ignore outdated build info file
        if version != '# Sphinx build info version 2':
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
        return build_info

    def __init__(
        self,
        config: Config | None = None,
        tags: Tags | None = None,
        config_categories: Set[_ConfigRebuild] = frozenset(),
    ) -> None:
        self.config_hash = ''
        self.tags_hash = ''

        if config:
            values = {c.name: c.value for c in config.filter(config_categories)}
            self.config_hash = _stable_str(values)

        if tags:
            self.tags_hash = _stable_str(sorted(tags))

    def __eq__(self, other: BuildInfo) -> bool:  # type: ignore[override]
        return (self.config_hash == other.config_hash
                and self.tags_hash == other.tags_hash)

    def dump(self, filename: Path, /) -> None:
        build_info = (
            '# Sphinx build info version 2\n'
            '# This file records the configuration used when building these files. '
            'When it is not found, a full rebuild will be done.\n'
            f'config: {self.config_hash}\n'
            f'tags: {self.tags_hash}\n'
        )
        filename.write_text(build_info, encoding="utf-8")

    def differing_keys(self, other: BuildInfo) -> list[str]:
        """Compute the keys that differ between two configs."""
        self_config = json.loads(self.config_hash)
        other_config = json.loads(other.config_hash)
        return [
            key
            for key in sorted(set(self_config) | set(other_config))
            if key not in self_config
            or key not in other_config
            or self_config[key] != other_config[key]
        ]


def _stable_str(obj: Any) -> str:
    """Return a stable string representation of a Python data structure.

    We can't just use str(obj) as the order of collections may be random.
    """
    return json.dumps(_json_prep(obj), separators=(',', ':'))


def _json_prep(obj: Any) -> dict[str, Any] | list[Any] | str:
    if isinstance(obj, dict):
        # convert to a sorted dict
        obj = {_json_prep(k): _json_prep(v) for k, v in obj.items()}
        obj = {k: obj[k] for k in sorted(obj, key=str)}
    elif isinstance(obj, list | tuple | set | frozenset):
        # convert to a sorted list
        obj = sorted(map(_json_prep, obj), key=str)
    elif isinstance(obj, type | types.FunctionType):
        # The default repr() of functions includes the ID, which is not ideal.
        # We use the fully qualified name instead.
        obj = f'{obj.__module__}.{obj.__qualname__}'
    else:
        # we can't do any better, just use the string representation
        obj = str(obj)
    return obj
