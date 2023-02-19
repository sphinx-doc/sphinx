"""File utility functions for Sphinx."""

from __future__ import annotations

import os
import posixpath
import warnings
from typing import TYPE_CHECKING, Callable

from docutils.utils import relative_path

from sphinx.deprecation import RemovedInSphinx80Warning
from sphinx.util.osutil import copyfile, ensuredir
from sphinx.util.typing import PathMatcher

if TYPE_CHECKING:
    from sphinx.util.template import BaseRenderer


def _template_basename(filename: str) -> str | None:
    # TODO: remove this method
    if filename.lower().endswith('_t'):
        warnings.warn(
            f"{filename!r}: filename suffix '_t' for templates is deprecated. "
            "If the file is a Jinja2 template, use the suffix '.jinja' instead.",
            RemovedInSphinx80Warning,
        )
        return filename[:-2]
    elif filename.lower().endswith(".jinja"):
        return filename[:-7]
    return None


def copy_asset_file(source: str, destination: str,
                    context: dict | None = None,
                    renderer: BaseRenderer | None = None) -> None:
    """Copy an asset file to destination.

    On copying, it expands the template variables if context argument is given and
    the asset is a template file.

    :param source: The path to source file
    :param destination: The path to destination file or directory
    :param context: The template variables.  If not given, template files are simply copied
    :param renderer: The template engine.  If not given, SphinxRenderer is used by default
    """
    if not os.path.exists(source):
        return

    if os.path.isdir(destination):
        # Use source filename if destination points a directory
        destination = os.path.join(destination, os.path.basename(source))

    if _template_basename(source) and context is not None:
        if renderer is None:
            from sphinx.util.template import SphinxRenderer
            renderer = SphinxRenderer()

        with open(source, encoding='utf-8') as fsrc:
            destination = _template_basename(destination) or destination
            with open(destination, 'w', encoding='utf-8') as fdst:
                fdst.write(renderer.render_string(fsrc.read(), context))
    else:
        copyfile(source, destination)


def copy_asset(source: str, destination: str, excluded: PathMatcher = lambda path: False,
               context: dict | None = None, renderer: BaseRenderer | None = None,
               onerror: Callable[[str, Exception], None] | None = None) -> None:
    """Copy asset files to destination recursively.

    On copying, it expands the template variables if context argument is given and
    the asset is a template file.

    :param source: The path to source file or directory
    :param destination: The path to destination directory
    :param excluded: The matcher to determine the given path should be copied or not
    :param context: The template variables.  If not given, template files are simply copied
    :param renderer: The template engine.  If not given, SphinxRenderer is used by default
    :param onerror: The error handler.
    """
    if not os.path.exists(source):
        return

    if renderer is None:
        from sphinx.util.template import SphinxRenderer
        renderer = SphinxRenderer()

    ensuredir(destination)
    if os.path.isfile(source):
        copy_asset_file(source, destination, context, renderer)
        return

    for root, dirs, files in os.walk(source, followlinks=True):
        reldir = relative_path(source, root)
        for dir in dirs[:]:
            if excluded(posixpath.join(reldir, dir)):
                dirs.remove(dir)
            else:
                ensuredir(posixpath.join(destination, reldir, dir))

        for filename in files:
            if not excluded(posixpath.join(reldir, filename)):
                try:
                    copy_asset_file(posixpath.join(root, filename),
                                    posixpath.join(destination, reldir),
                                    context, renderer)
                except Exception as exc:
                    if onerror:
                        onerror(posixpath.join(root, filename), exc)
                    else:
                        raise
