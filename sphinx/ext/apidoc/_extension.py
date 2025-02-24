"""Sphinx extension for auto-generating API documentation."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import TYPE_CHECKING

from sphinx._cli.util.colour import bold
from sphinx.ext.apidoc._generate import create_modules_toc_file, recurse_tree
from sphinx.ext.apidoc._shared import (
    LOGGER,
    ApidocDefaults,
    ApidocOptions,
    _remove_old_files,
)
from sphinx.locale import __

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from typing import Any

    from sphinx.application import Sphinx

_BOOL_KEYS = frozenset({
    'follow_links',
    'separate_modules',
    'include_private',
    'no_headings',
    'module_first',
    'implicit_namespaces',
})
_ALLOWED_KEYS = _BOOL_KEYS | frozenset({
    'path',
    'destination',
    'exclude_patterns',
    'automodule_options',
    'max_depth',
})


def run_apidoc(app: Sphinx) -> None:
    """Run the apidoc extension."""
    defaults = ApidocDefaults.from_config(app.config)
    apidoc_modules: Sequence[dict[str, Any]] = app.config.apidoc_modules
    srcdir: Path = app.srcdir
    confdir: Path = app.confdir

    LOGGER.info(bold(__('Running apidoc')))

    module_options: dict[str, Any]
    for i, module_options in enumerate(apidoc_modules):
        _run_apidoc_module(
            i,
            options=module_options,
            defaults=defaults,
            srcdir=srcdir,
            confdir=confdir,
        )


def _run_apidoc_module(
    i: int,
    *,
    options: dict[str, Any],
    defaults: ApidocDefaults,
    srcdir: Path,
    confdir: Path,
) -> None:
    """Run apidoc for a single module."""
    args = _parse_module_options(
        i, options=options, defaults=defaults, srcdir=srcdir, confdir=confdir
    )
    if args is None:
        return

    exclude_patterns_compiled: list[re.Pattern[str]] = [
        re.compile(fnmatch.translate(exclude)) for exclude in args.exclude_pattern
    ]

    written_files, modules = recurse_tree(
        args.module_path, exclude_patterns_compiled, args, args.template_dir
    )
    if args.toc_file:
        written_files.append(
            create_modules_toc_file(modules, args, args.toc_file, args.template_dir)
        )
    if args.remove_old:
        _remove_old_files(written_files, args.dest_dir, args.suffix)


def _parse_module_options(
    i: int,
    *,
    options: dict[str, Any],
    defaults: ApidocDefaults,
    srcdir: Path,
    confdir: Path,
) -> ApidocOptions | None:
    if not isinstance(options, dict):
        LOGGER.warning(__('apidoc_modules item %i must be a dict'), i, type='apidoc')
        return None

    # module path should be absolute or relative to the conf directory
    try:
        path = Path(options['path'])
    except KeyError:
        LOGGER.warning(
            __("apidoc_modules item %i must have a 'path' key"), i, type='apidoc'
        )
        return None
    except TypeError:
        LOGGER.warning(
            __("apidoc_modules item %i 'path' must be a string"), i, type='apidoc'
        )
        return None
    module_path = confdir / path
    if not module_path.is_dir():
        LOGGER.warning(
            __("apidoc_modules item %i 'path' is not an existing folder: %s"),
            i,
            module_path,
            type='apidoc',
        )
        return None

    # destination path should be relative to the source directory
    try:
        destination = Path(options['destination'])
    except KeyError:
        LOGGER.warning(
            __("apidoc_modules item %i must have a 'destination' key"),
            i,
            type='apidoc',
        )
        return None
    except TypeError:
        LOGGER.warning(
            __("apidoc_modules item %i 'destination' must be a string"),
            i,
            type='apidoc',
        )
        return None
    if destination.is_absolute():
        LOGGER.warning(
            __("apidoc_modules item %i 'destination' should be a relative path"),
            i,
            type='apidoc',
        )
        return None
    dest_path = srcdir / destination
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        LOGGER.warning(
            __('apidoc_modules item %i cannot create destination directory: %s'),
            i,
            exc.strerror,
            type='apidoc',
        )
        return None

    # exclude patterns should be absolute or relative to the conf directory
    exclude_patterns: list[str] = [
        str(confdir / pattern)
        for pattern in _check_collection_of_strings(
            i, options, key='exclude_patterns', default=defaults.exclude_patterns
        )
    ]

    # TODO template_dir

    max_depth = defaults.max_depth
    if 'max_depth' in options:
        if not isinstance(options['max_depth'], int):
            LOGGER.warning(
                __("apidoc_modules item %i '%s' must be an int"),
                i,
                'max_depth',
                type='apidoc',
            )
        else:
            max_depth = options['max_depth']

    bool_options: dict[str, bool] = {}
    for key in sorted(_BOOL_KEYS):
        if key not in options:
            bool_options[key] = getattr(defaults, key)
        elif not isinstance(options[key], bool):
            LOGGER.warning(
                __("apidoc_modules item %i '%s' must be a boolean"),
                i,
                key,
                type='apidoc',
            )
            bool_options[key] = getattr(defaults, key)
        else:
            bool_options[key] = options[key]

    # TODO per-module automodule_options
    automodule_options = frozenset(
        _check_collection_of_strings(
            i, options, key='automodule_options', default=defaults.automodule_options
        )
    )

    if diff := options.keys() - _ALLOWED_KEYS:
        LOGGER.warning(
            __('apidoc_modules item %i has unexpected keys: %s'),
            i,
            ', '.join(sorted(diff)),
            type='apidoc',
        )

    return ApidocOptions(
        dest_dir=dest_path,
        module_path=module_path,
        exclude_pattern=exclude_patterns,
        automodule_options=automodule_options,
        max_depth=max_depth,
        quiet=True,
        header=module_path.name,
        follow_links=bool_options['follow_links'],
        separate_modules=bool_options['separate_modules'],
        include_private=bool_options['include_private'],
        no_headings=bool_options['no_headings'],
        module_first=bool_options['module_first'],
        implicit_namespaces=bool_options['implicit_namespaces'],
    )


def _check_collection_of_strings(
    index: int,
    options: dict[str, Any],
    *,
    key: str,
    default: Collection[str],
) -> Collection[str]:
    """Check that a key's value is a collection of strings in the options.

    :returns: The value of the key, or None if invalid.
    """
    if key not in options:
        return default
    if not isinstance(options[key], list | tuple | set | frozenset):
        LOGGER.warning(
            __("apidoc_modules item %i '%s' must be a sequence"),
            index,
            key,
            type='apidoc',
        )
        return default
    for item in options[key]:
        if not isinstance(item, str):
            LOGGER.warning(
                __("apidoc_modules item %i '%s' must contain strings"),
                index,
                key,
                type='apidoc',
            )
            return default
    return options[key]
