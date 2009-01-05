# -*- coding: utf-8 -*-
"""
    sphinx.theming
    ~~~~~~~~~~~~~~

    Theming support for HTML builders.

    :copyright: 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import ConfigParser
from os import path

from sphinx.application import SphinxError


THEMECONF = 'theme.conf'

class ThemeError(SphinxError):
    category = 'Theme error'


class Theme(object):
    """
    Represents the theme chosen in the configuration.
    """
    @classmethod
    def init_themes(cls, builder):
        """Search all theme paths for available themes."""
        cls.themes = {}

        cls.themepath = list(builder.config.html_theme_path)
        cls.themepath.append(
            path.join(path.abspath(path.dirname(__file__)), 'themes'))

        for themedir in cls.themepath[::-1]:
            themedir = path.join(builder.confdir, themedir)
            if not path.isdir(themedir):
                continue
            for theme in os.listdir(themedir):
                if not path.isfile(path.join(themedir, theme, THEMECONF)):
                    continue
                cls.themes[theme] = path.join(themedir, theme)

    def __init__(self, name):
        if name not in self.themes:
            raise ThemeError('no theme named %r found' % name)
        self.name = name
        self.themedir = self.themes[name]

        self.themeconf = ConfigParser.RawConfigParser()
        self.themeconf.read(path.join(self.themedir, THEMECONF))

        inherit = self.themeconf.get('theme', 'inherit')
        if inherit == 'none':
            self.base = None
        elif inherit not in self.themes:
            raise ThemeError('no theme named %r found, inherited by %r' %
                             (inherit, name))
        else:
            self.base = Theme(inherit)

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
