"""Italian search language: includes the JS Italian stemmer."""

from __future__ import annotations

import snowballstemmer

from sphinx.search import SearchLanguage
from sphinx.search._stopwords.it import ITALIAN_STOPWORDS


class SearchItalian(SearchLanguage):
    lang = 'it'
    language_name = 'Italian'
    js_stemmer_rawcode = 'italian-stemmer.js'
    stopwords = ITALIAN_STOPWORDS

    def init(self, options: dict[str, str]) -> None:
        self.stemmer = snowballstemmer.stemmer('italian')

    def stem(self, word: str) -> str:
        return self.stemmer.stemWord(word.lower())
