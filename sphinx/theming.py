# -*- coding: utf-8 -*-
"""
    sphinx.theming
    ~~~~~~~~~~~~~~

    Theming support for HTML builders.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import shutil
import zipfile
import tempfile
import ConfigParser
from os import path

from sphinx import package_dir
from sphinx.errors import ThemeError


NODEFAULT = object()
THEMECONF = 'theme.conf'

class Theme(object):
    """
    Represents the theme chosen in the configuration.
    """
    themes = {}

    @classmethod
    def init_themes(cls, builder):
        """Search all theme paths for available themes."""
        cls.themepath = list(builder.config.html_theme_path)
        cls.themepath.append(path.join(package_dir, 'themes'))

        for themedir in cls.themepath[::-1]:
            themedir = path.join(builder.confdir, themedir)
            if not path.isdir(themedir):
                continue
            for theme in os.listdir(themedir):
                if theme.lower().endswith('.zip'):
                    try:
                        zfile = zipfile.ZipFile(path.join(themedir, theme))
                        if THEMECONF not in zfile.namelist():
                            continue
                        tname = theme[:-4]
                        tinfo = zfile
                    except Exception:
                        builder.warn('file %r on theme path is not a valid '
                                     'zipfile or contains no theme' % theme)
                        continue
                else:
                    if not path.isfile(path.join(themedir, theme, THEMECONF)):
                        continue
                    tname = theme
                    tinfo = None
                cls.themes[tname] = (path.join(themedir, theme), tinfo)

    def __init__(self, name):
        if name not in self.themes:
            raise ThemeError('no theme named %r found '
                             '(missing theme.conf?)' % name)
        self.name = name

        tdir, tinfo = self.themes[name]
        if tinfo is None:
            # already a directory, do nothing
            self.themedir = tdir
            self.themedir_created = False
        else:
            # extract the theme to a temp directory
            self.themedir = tempfile.mkdtemp('sxt')
            self.themedir_created = True
            for name in tinfo.namelist():
                if name.endswith('/'): continue
                dirname = path.dirname(name)
                if not path.isdir(path.join(self.themedir, dirname)):
                    os.makedirs(path.join(self.themedir, dirname))
                fp = open(path.join(self.themedir, name), 'wb')
                fp.write(tinfo.read(name))
                fp.close()

        self.themeconf = ConfigParser.RawConfigParser()
        self.themeconf.read(path.join(self.themedir, THEMECONF))

        try:
            inherit = self.themeconf.get('theme', 'inherit')
        except ConfigParser.NoOptionError:
            raise ThemeError('theme %r doesn\'t have "inherit" setting' % name)
        if inherit == 'none':
            self.base = None
        elif inherit not in self.themes:
            raise ThemeError('no theme named %r found, inherited by %r' %
                             (inherit, name))
        else:
            self.base = Theme(inherit)

    def get_confstr(self, section, name, default=NODEFAULT):
        """
        Return the value for a theme configuration setting, searching the
        base theme chain.
        """
        try:
            return self.themeconf.get(section, name)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            if self.base is not None:
                return self.base.get_confstr(section, name, default)
            if default is NODEFAULT:
                raise ThemeError('setting %s.%s occurs in none of the '
                                 'searched theme configs' % (section, name))
            else:
                return default

    def get_options(self, overrides):
        """
        Return a dictionary of theme options and their values.
        """
        chain = [self.themeconf]
        base = self.base
        while base is not None:
            chain.append(base.themeconf)
            base = base.base
        options = {}
        for conf in reversed(chain):
            try:
                options.update(conf.items('options'))
            except ConfigParser.NoSectionError:
                pass
        for option, value in overrides.iteritems():
            if option not in options:
                raise ThemeError('unsupported theme option %r given' % option)
            options[option] = value
        return options

    def get_dirchain(self):
        """
        Return a list of theme directories, beginning with this theme's,
        then the base theme's, then that one's base theme's, etc.
        """
        chain = [self.themedir]
        base = self.base
        while base is not None:
            chain.append(base.themedir)
            base = base.base
        return chain

    def cleanup(self):
        """
        Remove temporary directories.
        """
        if self.themedir_created:
            try:
                shutil.rmtree(self.themedir)
            except Exception:
                pass
        if self.base:
            self.base.cleanup()
