"""German search language: includes the JS German stemmer."""

from __future__ import annotations

import snowballstemmer

from sphinx.search import SearchLanguage
from sphinx.search._stopwords.de import GERMAN_STOPWORDS


class SearchGerman(SearchLanguage):
    lang = 'de'
    language_name = 'German'
    js_stemmer_rawcode = 'german-stemmer.js'
    stopwords = GERMAN_STOPWORDS

    def init(self, options: dict[str, str]) -> None:
        self.stemmer = snowballstemmer.stemmer('german')

    def stem(self, word: str) -> str:
        return self.stemmer.stemWord(word.lower())
