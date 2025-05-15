"""Spanish search language: includes the JS Spanish stemmer."""

from __future__ import annotations

import snowballstemmer

from sphinx.search import SearchLanguage
from sphinx.search._stopwords.es import SPANISH_STOPWORDS


class SearchSpanish(SearchLanguage):
    lang = 'es'
    language_name = 'Spanish'
    js_stemmer_rawcode = 'spanish-stemmer.js'
    stopwords = SPANISH_STOPWORDS

    def init(self, options: dict[str, str]) -> None:
        self.stemmer = snowballstemmer.stemmer('spanish')

    def stem(self, word: str) -> str:
        return self.stemmer.stemWord(word.lower())
