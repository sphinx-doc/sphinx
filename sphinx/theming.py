# -*- coding: utf-8 -*-
"""
    sphinx.theming
    ~~~~~~~~~~~~~~

    Theming support for HTML builders.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import shutil
import tempfile
from os import path
from zipfile import ZipFile

import pkg_resources
from six import string_types, iteritems
from six.moves import configparser

from sphinx import package_dir
from sphinx.errors import ThemeError
from sphinx.locale import _
from sphinx.util import logging
from sphinx.util.osutil import ensuredir

logger = logging.getLogger(__name__)

if False:
    # For type annotation
    from typing import Any, Dict, Iterator, List, Tuple  # NOQA

NODEFAULT = object()
THEMECONF = 'theme.conf'


class _Theme(object):
    def __init__(self):
        # type: () -> None
        self.name = None
        self.base = None
        self.themedir = None
        self.themeconf = None

    @property
    def dirs(self):
        # type: () -> List[unicode]
        """Return a list of theme directories, beginning with this theme's,
        then the base theme's, then that one's base theme's, etc.
        """
        if self.base is None:
            return [self.themedir]
        else:
            return [self.themedir] + self.base.get_dirchain()

    def get_dirchain(self):
        # type: () -> List[unicode]
        """Return a list of theme directories, beginning with this theme's,
        then the base theme's, then that one's base theme's, etc.
        """
        return self.dirs

    def get_config(self, section, name, default=NODEFAULT):
        # type: (unicode, unicode, Any) -> Any
        """Return the value for a theme configuration setting, searching the
        base theme chain.
        """
        try:
            return self.themeconf.get(section, name)  # type: ignore
        except (configparser.NoOptionError, configparser.NoSectionError):
            if self.base:
                return self.base.get_config(section, name, default)

            if default is NODEFAULT:
                raise ThemeError(_('setting %s.%s occurs in none of the '
                                   'searched theme configs') % (section, name))
            else:
                return default

    def get_confstr(self, section, name, default=NODEFAULT):
        # type: (unicode, unicode, Any) -> Any
        """Return the value for a theme configuration setting, searching the
        base theme chain.
        """
        return self.get_config(section, name, default)

    def get_options(self, overrides={}):
        # type: (Dict[unicode, Any]) -> Dict[unicode, Any]
        """Return a dictionary of theme options and their values."""
        if self.base:
            options = self.base.get_options()
        else:
            options = {}  # type: Dict[unicode, Any]

        try:
            options.update(self.themeconf.items('options'))
        except configparser.NoSectionError:
            pass

        for option, value in iteritems(overrides):
            if option not in options:
                raise ThemeError('unsupported theme option %r given' % option)
            options[option] = value

        return options

    def cleanup(self):
        # type: () -> None
        """Remove temporary directories."""
        if self.themedir_created:
            try:
                shutil.rmtree(self.rootdir)
            except Exception:
                pass
        if self.base:
            self.base.cleanup()


def is_archived_theme(filename):
    # type: (unicode) -> bool
    try:
        with ZipFile(filename) as f:  # type: ignore
            return THEMECONF in f.namelist()
    except:
        return False


def find_theme_entries(themedir):
    # type: (unicode) -> Iterator[Tuple[unicode, unicode]]
    for entry in os.listdir(themedir):
        pathname = path.join(themedir, entry)
        if path.isfile(pathname) and entry.lower().endswith('.zip'):
            if is_archived_theme(pathname):
                name = entry[:-4]
                yield name, pathname
            else:
                logger.warning(_('file %r on theme path is not a valid '
                                 'zipfile or contains no theme'), entry)
        else:
            if path.isfile(path.join(pathname, THEMECONF)):
                yield entry, pathname


class Theme(object):
    """
    Represents the theme chosen in the configuration.
    """
    themes = {}     # type: Dict[unicode, unicode]

    @classmethod
    def init_themes(cls, confdir, theme_path):
        # type: (unicode, unicode) -> None
        """Search all theme paths for available themes."""
        themepath = list(theme_path)
        themepath.append(path.join(package_dir, 'themes'))

        # search themes from theme_paths
        for themedir in themepath:
            themedir = path.abspath(path.join(confdir, themedir))
            if not path.isdir(themedir):
                continue
            else:
                for name, theme in find_theme_entries(themedir):
                    cls.themes[name] = theme

    @classmethod
    def load_extra_theme(cls, name):
        if name == 'alabaster':
            cls.load_alabaster()
        elif name == 'sphinx_rtd_theme':
            cls.load_sphinx_rtd_theme()
        else:
            pass

    @classmethod
    def load_alabaster(cls):
        import alabaster
        cls.themes['alabaster'] = path.join(alabaster.get_path(), 'alabaster')

    @classmethod
    def load_sphinx_rtd_theme(cls):
        try:
            import sphinx_rtd_theme
            cls.themes['sphinx_rtd_theme'] = path.join(sphinx_rtd_theme.get_html_theme_path(),
                                                       'sphinx_rtd_theme')
        except ImportError:
            pass

    @classmethod
    def load_external_themes(cls, name):
        for entry_point in pkg_resources.iter_entry_points('sphinx_themes'):
            target = entry_point.load()
            if callable(target):
                themedir = target()
                if not isinstance(path, string_types):
                    logger.warning(_('Theme extension %r does not response correctly.') %
                                   entry_point.module_name)
            else:
                themedir = target

            for entry, theme in find_theme_entries(themedir):
                if name == entry:
                    cls.themes[entry] = theme

    @classmethod
    def create(cls, name):
        # type: (unicode) -> None
        if name not in cls.themes:
            cls.load_extra_theme(name)

        if name not in cls.themes:
            if name == 'sphinx_rtd_theme':
                raise ThemeError(_('sphinx_rtd_theme is no longer a hard dependency '
                                   'since version 1.4.0. Please install it manually.'
                                   '(pip install sphinx_rtd_theme)'))
            else:
                raise ThemeError(_('no theme named %r found '
                                   '(missing theme.conf?)') % name)

        theme = _Theme()
        theme.name = name

        themedir = cls.themes[name]
        if path.isdir(themedir):
            # already a directory, do nothing
            theme.rootdir = None
            theme.themedir = themedir
            theme.themedir_created = False
        else:
            # extract the theme to a temp directory
            theme.rootdir = tempfile.mkdtemp('sxt')
            theme.themedir = path.join(theme.rootdir, name)
            theme.themedir_created = True
            ensuredir(theme.themedir)

            with ZipFile(themedir) as archive:  # type: ignore
                for name in archive.namelist():
                    if name.endswith('/'):
                        continue
                    filename = path.join(theme.themedir, name)
                    ensuredir(path.dirname(filename))
                    with open(path.join(filename), 'wb') as fp:
                        fp.write(archive.read(name))

        theme.themeconf = configparser.RawConfigParser()
        theme.themeconf.read(path.join(theme.themedir, THEMECONF))  # type: ignore

        try:
            inherit = theme.themeconf.get('theme', 'inherit')
        except configparser.NoOptionError:
            raise ThemeError('theme %r doesn\'t have "inherit" setting' % name)

        if inherit == 'none':
            theme.base = None
        elif inherit not in cls.themes:
            raise ThemeError('no theme named %r found, inherited by %r' %
                             (inherit, name))
        else:
            theme.base = cls.create(inherit)

        return theme
