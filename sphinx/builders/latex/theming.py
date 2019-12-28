"""
    sphinx.builders.latex.theming
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Theming support for LaTeX builder.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import configparser
from os import path
from typing import Dict

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.errors import ThemeError
from sphinx.locale import __
from sphinx.util import logging

logger = logging.getLogger(__name__)


class Theme:
    """A set of LaTeX configurations."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.docclass = name
        self.wrapperclass = name
        self.toplevel_sectioning = 'chapter'


class BuiltInTheme(Theme):
    """A built-in LaTeX theme."""

    def __init__(self, name: str, config: Config) -> None:
        # Note: Don't call supermethod here.
        self.name = name
        self.latex_docclass = config.latex_docclass  # type: Dict[str, str]

    @property
    def docclass(self) -> str:  # type: ignore
        if self.name == 'howto':
            return self.latex_docclass.get('howto', 'article')
        else:
            return self.latex_docclass.get('manual', 'report')

    @property
    def wrapperclass(self) -> str:  # type: ignore
        if self.name in ('manual', 'howto'):
            return 'sphinx' + self.name
        else:
            return self.name

    @property
    def toplevel_sectioning(self) -> str:  # type: ignore
        # we assume LaTeX class provides \chapter command except in case
        # of non-Japanese 'howto' case
        if self.name == 'howto' and not self.docclass.startswith('j'):
            return 'section'
        else:
            return 'chapter'


class UserTheme(Theme):
    """A user defined LaTeX theme."""

    def __init__(self, name: str, filename: str) -> None:
        self.name = name
        self.config = configparser.RawConfigParser()
        self.config.read(path.join(filename))

        try:
            self.docclass = self.config.get('theme', 'docclass')
            self.wrapperclass = self.config.get('theme', 'wrapperclass')
            self.toplevel_sectioning = self.config.get('theme', 'toplevel_sectioning')
        except configparser.NoSectionError:
            raise ThemeError(__('%r doesn\'t have "theme" setting') % filename)
        except configparser.NoOptionError as exc:
            raise ThemeError(__('%r doesn\'t have "%s" setting') % (filename, exc.args[0]))


class ThemeFactory:
    """A factory class for LaTeX Themes."""

    def __init__(self, app: Sphinx) -> None:
        self.themes = {}  # type: Dict[str, Theme]
        self.theme_paths = [path.join(app.srcdir, p) for p in app.config.latex_theme_path]
        self.load_builtin_themes(app.config)

    def load_builtin_themes(self, config: Config) -> None:
        """Load built-in themes."""
        self.themes['manual'] = BuiltInTheme('manual', config)
        self.themes['howto'] = BuiltInTheme('howto', config)

    def get(self, name: str) -> Theme:
        """Get a theme for given *name*."""
        if name in self.themes:
            return self.themes[name]
        else:
            theme = self.find_user_theme(name)
            if theme:
                return theme
            else:
                return Theme(name)

    def find_user_theme(self, name: str) -> Theme:
        """Find a theme named as *name* from latex_theme_path."""
        for theme_path in self.theme_paths:
            config_path = path.join(theme_path, name, 'theme.conf')
            if path.isfile(config_path):
                try:
                    return UserTheme(name, config_path)
                except ThemeError as exc:
                    logger.warning(exc)

        return None
