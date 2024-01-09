"""Theming support for HTML builders."""

from __future__ import annotations

import configparser
import contextlib
import os
import shutil
import sys
import tempfile
from os import path
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

from sphinx import package_dir
from sphinx.config import check_confval_types as _config_post_init
from sphinx.errors import ThemeError
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.osutil import ensuredir

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = 'Theme', 'HTMLThemeFactory'

logger = logging.getLogger(__name__)

_NO_DEFAULT = object()
_THEME_CONF = 'theme.conf'


def _extract_zip(filename: str, target_dir: str, /) -> None:
    """Extract zip file to target directory."""
    ensuredir(target_dir)

    with ZipFile(filename) as archive:
        for name in archive.namelist():
            if name.endswith('/'):
                continue
            entry = path.join(target_dir, name)
            ensuredir(path.dirname(entry))
            with open(path.join(entry), 'wb') as fp:
                fp.write(archive.read(name))


def _load_theme_conf(theme_dir: os.PathLike[str] | str) -> configparser.RawConfigParser:
    c = configparser.RawConfigParser()
    config_file_path = path.join(theme_dir, _THEME_CONF)
    if not os.path.isfile(config_file_path):
        raise ThemeError(__('theme configuration file %r not found') % config_file_path)
    c.read(config_file_path, encoding='utf-8')
    return c


class Theme:
    """A Theme is a set of HTML templates and configurations.

    This class supports both theme directory and theme archive (zipped theme).
    """

    def __init__(self, name: str, theme_path: str, theme_factory: HTMLThemeFactory) -> None:
        self.name = name
        self._base: Theme | None = None

        if path.isdir(theme_path):
            # already a directory, do nothing
            self._root_dir = None
            self._theme_dir = theme_path
        else:
            # extract the theme to a temp directory
            self._root_dir = tempfile.mkdtemp('sxt')
            self._theme_dir = path.join(self._root_dir, name)
            _extract_zip(theme_path, self._theme_dir)

        self.config = _load_theme_conf(self._theme_dir)

        try:
            inherit = self.config.get('theme', 'inherit')
        except configparser.NoSectionError as exc:
            raise ThemeError(__('theme %r doesn\'t have "theme" setting') % name) from exc
        except configparser.NoOptionError as exc:
            raise ThemeError(__('theme %r doesn\'t have "inherit" setting') % name) from exc
        self._load_ancestor_theme(inherit, theme_factory, name)

        try:
            self._options = dict(self.config.items('options'))
        except configparser.NoSectionError:
            self._options = {}

        self.inherit = inherit
        try:
            self.stylesheet = self.get_config('theme', 'stylesheet')
        except configparser.NoOptionError:
            msg = __("No loaded theme defines 'theme.stylesheet' in the configuration")
            raise ThemeError(msg) from None
        self.sidebars = self.get_config('theme', 'sidebars', None)
        self.pygments_style = self.get_config('theme', 'pygments_style', None)
        self.pygments_dark_style = self.get_config('theme', 'pygments_dark_style', None)

    def _load_ancestor_theme(
        self,
        inherit: str,
        theme_factory: HTMLThemeFactory,
        name: str,
    ) -> None:
        if inherit != 'none':
            try:
                self._base = theme_factory.create(inherit)
            except ThemeError as exc:
                raise ThemeError(__('no theme named %r found, inherited by %r') %
                                 (inherit, name)) from exc

    def get_theme_dirs(self) -> list[str]:
        """Return a list of theme directories, beginning with this theme's,
        then the base theme's, then that one's base theme's, etc.
        """
        if self._base is None:
            return [self._theme_dir]
        else:
            return [self._theme_dir] + self._base.get_theme_dirs()

    def get_config(self, section: str, name: str, default: Any = _NO_DEFAULT) -> Any:
        """Return the value for a theme configuration setting, searching the
        base theme chain.
        """
        try:
            return self.config.get(section, name)
        except (configparser.NoOptionError, configparser.NoSectionError):
            if self._base:
                return self._base.get_config(section, name, default)

            if default is _NO_DEFAULT:
                raise ThemeError(__('setting %s.%s occurs in none of the '
                                    'searched theme configs') % (section, name)) from None
            return default

    def get_options(self, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return a dictionary of theme options and their values."""
        if overrides is None:
            overrides = {}

        if self._base is not None:
            options = self._base.get_options()
        else:
            options = {}
        options |= self._options

        for option, value in overrides.items():
            if option not in options:
                logger.warning(__('unsupported theme option %r given') % option)
            else:
                options[option] = value

        return options

    def _cleanup(self) -> None:
        """Remove temporary directories."""
        if self._root_dir:
            with contextlib.suppress(Exception):
                shutil.rmtree(self._root_dir)

        if self._base is not None:
            self._base._cleanup()


def _is_archived_theme(filename: str, /) -> bool:
    """Check whether the specified file is an archived theme file or not."""
    try:
        with ZipFile(filename) as f:
            return _THEME_CONF in f.namelist()
    except Exception:
        return False


class HTMLThemeFactory:
    """A factory class for HTML Themes."""

    def __init__(self, app: Sphinx) -> None:
        self._app = app
        self._themes = app.registry.html_themes
        self._load_builtin_themes()
        if getattr(app.config, 'html_theme_path', None):
            self._load_additional_themes(app.config.html_theme_path)

    def _load_builtin_themes(self) -> None:
        """Load built-in themes."""
        themes = self._find_themes(path.join(package_dir, 'themes'))
        for name, theme in themes.items():
            self._themes[name] = theme

    def _load_additional_themes(self, theme_paths: str) -> None:
        """Load additional themes placed at specified directories."""
        for theme_path in theme_paths:
            abs_theme_path = path.abspath(path.join(self._app.confdir, theme_path))
            themes = self._find_themes(abs_theme_path)
            for name, theme in themes.items():
                self._themes[name] = theme

    def _load_extra_theme(self, name: str) -> None:
        """Try to load a theme with the specified name.

        This uses the ``sphinx.html_themes`` entry point from package metadata.
        """
        theme_entry_points = entry_points(group='sphinx.html_themes')
        try:
            entry_point = theme_entry_points[name]
        except KeyError:
            pass
        else:
            self._app.registry.load_extension(self._app, entry_point.module)
            _config_post_init(None, self._app.config)

    def _find_themes(self, theme_path: str) -> dict[str, str]:
        """Search themes from specified directory."""
        themes: dict[str, str] = {}
        if not path.isdir(theme_path):
            return themes

        for entry in os.listdir(theme_path):
            pathname = path.join(theme_path, entry)
            if path.isfile(pathname) and entry.lower().endswith('.zip'):
                if _is_archived_theme(pathname):
                    name = entry[:-4]
                    themes[name] = pathname
                else:
                    logger.warning(__('file %r on theme path is not a valid '
                                      'zipfile or contains no theme'), entry)
            else:
                if path.isfile(path.join(pathname, _THEME_CONF)):
                    themes[entry] = pathname

        return themes

    def create(self, name: str) -> Theme:
        """Create an instance of theme."""
        if name not in self._themes:
            self._load_extra_theme(name)

        if name not in self._themes:
            raise ThemeError(__('no theme named %r found (missing theme.conf?)') % name)

        return Theme(name, self._themes[name], self)
