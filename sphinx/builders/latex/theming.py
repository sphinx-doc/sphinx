"""
    sphinx.builders.latex.theming
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Theming support for LaTeX builder.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Dict

from sphinx.application import Sphinx
from sphinx.config import Config


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


class ThemeFactory:
    """A factory class for LaTeX Themes."""

    def __init__(self, app: Sphinx) -> None:
        self.themes = {}  # type: Dict[str, Theme]
        self.load_builtin_themes(app.config)

    def load_builtin_themes(self, config: Config) -> None:
        """Load built-in themes."""
        self.themes['manual'] = BuiltInTheme('manual', config)
        self.themes['howto'] = BuiltInTheme('howto', config)

    def get(self, name: str) -> Theme:
        """Get a theme for given *name*."""
        if name not in self.themes:
            return Theme(name)
        else:
            return self.themes[name]
