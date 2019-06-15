"""
    sphinx.builders.latex.util
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for LaTeX builder.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from docutils.writers.latex2e import Babel

from sphinx.deprecation import RemovedInSphinx30Warning


class ExtBabel(Babel):
    cyrillic_languages = ('bulgarian', 'kazakh', 'mongolian', 'russian', 'ukrainian')

    def __init__(self, language_code: str, use_polyglossia: bool = False) -> None:
        self.language_code = language_code
        self.use_polyglossia = use_polyglossia
        self.supported = True
        super().__init__(language_code or '')

    def get_shorthandoff(self) -> str:
        warnings.warn('ExtBabel.get_shorthandoff() is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)
        from sphinx.writers.latex import SHORTHANDOFF
        return SHORTHANDOFF

    def uses_cyrillic(self) -> bool:
        return self.language in self.cyrillic_languages

    def is_supported_language(self) -> bool:
        return self.supported

    def language_name(self, language_code: str) -> str:
        language = super().language_name(language_code)
        if language == 'ngerman' and self.use_polyglossia:
            # polyglossia calls new orthography (Neue Rechtschreibung) as
            # german (with new spelling option).
            return 'german'
        elif language:
            return language
        elif language_code.startswith('zh'):
            return 'english'  # fallback to english (behaves like supported)
        else:
            self.supported = False
            return 'english'  # fallback to english

    def get_mainlanguage_options(self) -> str:
        """Return options for polyglossia's ``\\setmainlanguage``."""
        if self.use_polyglossia is False:
            return None
        elif self.language == 'german':
            language = super().language_name(self.language_code)
            if language == 'ngerman':
                return 'spelling=new'
            else:
                return 'spelling=old'
        else:
            return None
