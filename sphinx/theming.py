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
import zipfile
import tempfile
from os import path

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
    from typing import Any, Callable, Dict, List, Tuple  # NOQA

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


class Theme(object):
    """
    Represents the theme chosen in the configuration.
    """
    themes = {}     # type: Dict[unicode, Tuple[unicode, zipfile.ZipFile]]
    themepath = []  # type: List[unicode]

    @classmethod
    def init_themes(cls, confdir, theme_path):
        # type: (unicode, unicode) -> None
        """Search all theme paths for available themes."""
        cls.themepath = list(theme_path)
        cls.themepath.append(path.join(package_dir, 'themes'))

        for themedir in cls.themepath[::-1]:
            themedir = path.join(confdir, themedir)
            if not path.isdir(themedir):
                continue
            for theme in os.listdir(themedir):
                if theme.lower().endswith('.zip'):
                    try:
                        zfile = zipfile.ZipFile(path.join(themedir, theme))  # type: ignore
                        if THEMECONF not in zfile.namelist():
                            continue
                        tname = theme[:-4]
                        tinfo = zfile
                    except Exception:
                        logger.warning('file %r on theme path is not a valid '
                                       'zipfile or contains no theme', theme)
                        continue
                else:
                    if not path.isfile(path.join(themedir, theme, THEMECONF)):
                        continue
                    tname = theme
                    tinfo = None
                cls.themes[tname] = (path.join(themedir, theme), tinfo)

    @classmethod
    def load_extra_theme(cls, name):
        # type: (unicode) -> None
        themes = ['alabaster']
        try:
            import sphinx_rtd_theme
            themes.append('sphinx_rtd_theme')
        except ImportError:
            pass
        if name in themes:
            if name == 'alabaster':
                import alabaster
                themedir = alabaster.get_path()
                # alabaster theme also requires 'alabaster' extension, it will be loaded
                # at sphinx.application module.
            elif name == 'sphinx_rtd_theme':
                themedir = sphinx_rtd_theme.get_html_theme_path()
            else:
                raise NotImplementedError('Programming Error')

        else:
            for themedir in load_theme_plugins():
                if path.isfile(path.join(themedir, name, THEMECONF)):
                    break
            else:
                # specified theme is not found
                return

        cls.themepath.append(themedir)
        cls.themes[name] = (path.join(themedir, name), None)
        return

    @classmethod
    def create(cls, name):
        # type: (unicode) -> None
        if name not in cls.themes:
            cls.load_extra_theme(name)
            if name not in cls.themes:
                if name == 'sphinx_rtd_theme':
                    raise ThemeError('sphinx_rtd_theme is no longer a hard dependency '
                                     'since version 1.4.0. Please install it manually.'
                                     '(pip install sphinx_rtd_theme)')
                else:
                    raise ThemeError('no theme named %r found '
                                     '(missing theme.conf?)' % name)

        theme = _Theme()
        theme.name = name

        # Do not warn yet -- to be compatible with old Sphinxes, people *have*
        # to use "default".
        # if name == 'default' and warn:
        #     warn("'default' html theme has been renamed to 'classic'. "
        #          "Please change your html_theme setting either to "
        #          "the new 'alabaster' default theme, or to 'classic' "
        #          "to keep using the old default.")

        tdir, tinfo = cls.themes[name]
        if tinfo is None:
            # already a directory, do nothing
            theme.rootdir = None
            theme.themedir = tdir
            theme.themedir_created = False
        else:
            # extract the theme to a temp directory
            theme.rootdir = tempfile.mkdtemp('sxt')
            theme.themedir = path.join(theme.rootdir, name)
            theme.themedir_created = True
            ensuredir(theme.themedir)

            for name in tinfo.namelist():
                if name.endswith('/'):
                    continue
                dirname = path.dirname(name)
                if not path.isdir(path.join(theme.themedir, dirname)):
                    os.makedirs(path.join(theme.themedir, dirname))
                with open(path.join(theme.themedir, name), 'wb') as fp:
                    fp.write(tinfo.read(name))

        theme.themeconf = configparser.RawConfigParser()
        theme.themeconf.read(path.join(theme.themedir, THEMECONF))  # type: ignore

        try:
            inherit = theme.themeconf.get('theme', 'inherit')
        except configparser.NoOptionError:
            raise ThemeError('theme %r doesn\'t have "inherit" setting' % name)

        # load inherited theme automatically #1794, #1884, #1885
        cls.load_extra_theme(inherit)

        if inherit == 'none':
            theme.base = None
        elif inherit not in cls.themes:
            raise ThemeError('no theme named %r found, inherited by %r' %
                             (inherit, name))
        else:
            theme.base = cls.create(inherit)

        return theme


def load_theme_plugins():
    # type: () -> List[unicode]
    """load plugins by using``sphinx_themes`` section in setuptools entry_points.
    This API will return list of directory that contain some theme directory.
    """
    theme_paths = []  # type: List[unicode]

    for plugin in pkg_resources.iter_entry_points('sphinx_themes'):
        func_or_path = plugin.load()
        try:
            path = func_or_path()
        except Exception:
            path = func_or_path

        if isinstance(path, string_types):
            theme_paths.append(path)
        else:
            raise ThemeError('Plugin %r does not response correctly.' %
                             plugin.module_name)

    return theme_paths
