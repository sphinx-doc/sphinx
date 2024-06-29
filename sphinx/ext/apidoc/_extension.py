"""Sphinx extension for auto-generating API documentation."""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sphinx.locale import __
from sphinx.util.console import bold

from . import WARNING_TYPE, _remove_old_files, create_modules_toc_file, logger, recurse_tree

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def run_apidoc_ext(app: Sphinx) -> None:
    """Run the apidoc extension."""
    logger.info(bold(__('Running apidoc')))  # TODO use iterater

    options: dict[str, Any]
    for i, options in enumerate(app.config.apidoc_modules):
        if not isinstance(options, dict):
            logger.warning(__('apidoc_modules item %i must be a dict'), i, type=WARNING_TYPE)
            continue

        # module path should be absolute or relative to the conf directory
        # TODO account for Windows path?
        if not (path := _check_string(i, options, 'path', True)):
            continue
        module_path = app.confdir.joinpath(path)
        if not module_path.is_dir():
            logger.warning(
                __("apidoc_modules item %i 'path' is not an existing folder: %s"),
                i,
                module_path,
                type=WARNING_TYPE,
            )
            continue

        # destination path should be relative to the source directory
        # TODO account for Windows path?
        if not (destination := _check_string(i, options, 'destination', True)):
            continue
        if os.path.isabs(destination):
            logger.warning(
                __("apidoc_modules item %i 'destination' should be a relative path"),
                i,
                type=WARNING_TYPE,
            )
            continue
        dest_path = app.srcdir.joinpath(destination)
        try:
            dest_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning(
                __('apidoc_modules item %i cannot create destination directory: %s'),
                i,
                exc.strerror,
                type=WARNING_TYPE,
            )
            continue

        # exclude patterns should be absolute or relative to the conf directory
        # TODO account for Windows path?
        exclude_patterns: list[str] = []
        exclude_patterns_compiled: list[re.Pattern[str]] = []
        for pattern in _check_list_of_strings(i, options, 'exclude_patterns') or []:
            exclude_path = app.confdir.joinpath(pattern)
            exclude_patterns.append(str(exclude_path))
            exclude_patterns_compiled.append(re.compile(fnmatch.translate(str(exclude_path))))

        # TODO template_dir

        maxdepth = 4
        if 'maxdepth' in options:
            if not isinstance(options['maxdepth'], int):
                logger.warning(
                    __("apidoc_modules item %i '%s' must be an int"),
                    i,
                    'maxdepth',
                    type=WARNING_TYPE,
                )
            else:
                maxdepth = options['maxdepth']

        extra_options = {}
        bool_keys = (
            'followlinks',
            'separatemodules',
            'includeprivate',
            'noheadings',
            'modulefirst',
            'implicit_namespaces',
        )
        for key in bool_keys:
            if key not in options:
                continue
            if not isinstance(options[key], bool):
                logger.warning(
                    __("apidoc_modules item %i '%s' must be a boolean"),
                    i,
                    key,
                    type=WARNING_TYPE,
                )
                continue
            extra_options[key] = options[key]

        # TODO per-module automodule_options
        automodule_options = ['members', 'undoc-members', 'show-inheritance']
        if (_options := _check_list_of_strings(i, options, 'automodule_options')) is not None:
            automodule_options = _options

        diff = (
            set(options)
            - {'path', 'destination', 'exclude_patterns', 'automodule_options', 'maxdepth'}
            - set(bool_keys)
        )
        if diff:
            logger.warning(
                __('apidoc_modules item %i has unexpected keys: %s'),
                i,
                ', '.join(diff),
                type=WARNING_TYPE,
            )

        args = ExtensionOptions(
            module_path=str(module_path),
            destdir=str(dest_path),
            exclude_pattern=exclude_patterns,
            automodule_options=automodule_options,
            maxdepth=maxdepth,
            quiet=True,
            **extra_options,
        )

        written_files, modules = recurse_tree(
            args.module_path, exclude_patterns_compiled, args, args.templatedir
        )
        if args.tocfile:
            written_files.append(
                create_modules_toc_file(modules, args, args.tocfile, args.templatedir)
            )
        if args.remove_old:
            _remove_old_files(written_files, args.destdir, args.suffix)


def _check_string(index: int, options: dict[str, Any], key: str, required: bool) -> str | None:
    """Check that a key's value is a string in the options.

    :returns: the value of the key, or None if missing or it is not a string
    """
    if key not in options:
        if required:
            logger.warning(
                __("apidoc_modules item %i must have a '%s' key"),
                index,
                key,
                type=WARNING_TYPE,
            )
        return None
    if not isinstance(options[key], str):
        logger.warning(
            __("apidoc_modules item %i '%s' must be a string"), index, type=WARNING_TYPE
        )
        return None
    return options[key]


def _check_list_of_strings(index: int, options: dict[str, Any], key: str) -> list[str] | None:
    """Check that a key's value is a list of strings in the options.

    :returns: the value of the key, or None if missing or it is not a string list
    """
    if key not in options:
        return None
    if not isinstance(options[key], list):
        logger.warning(
            __("apidoc_modules item %i '%s' must be a list"),
            index,
            key,
            type=WARNING_TYPE,
        )
        return None
    for item in options[key]:
        if not isinstance(item, str):
            logger.warning(
                __("apidoc_modules item %i '%s' must contain strings"),
                index,
                key,
                type=WARNING_TYPE,
            )
            return None
    return options[key]


@dataclass
class ExtensionOptions:
    """Options for the apidoc extension."""

    destdir: str
    module_path: str
    exclude_pattern: list[str]
    automodule_options: list[str] | None
    maxdepth: int
    followlinks: bool = False
    separatemodules: bool = False
    includeprivate: bool = False
    noheadings: bool = False
    modulefirst: bool = False
    implicit_namespaces: bool = False
    tocfile: str = 'modules'
    suffix: str = 'rst'
    header: str = ''
    templatedir: str | None = None

    remove_old: bool = True

    quiet: bool = False
    dryrun: bool = False
    force: bool = True

    full: bool = False
    author: str | None = None
    version: str | None = None
    release: str | None = None
    extensions: list[str] | None = None
    append_syspath: bool = False
