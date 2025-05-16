"""Norwegian search language: includes the JS Norwegian stemmer."""

from __future__ import annotations

import snowballstemmer

from sphinx.search import SearchLanguage
from sphinx.search._stopwords.no import NORWEGIAN_STOPWORDS


class SearchNorwegian(SearchLanguage):
    lang = 'no'
    language_name = 'Norwegian'
    js_stemmer_rawcode = 'norwegian-stemmer.js'
    stopwords = NORWEGIAN_STOPWORDS

    def init(self, options: dict[str, str]) -> None:
        self.stemmer = snowballstemmer.stemmer('norwegian')

    def stem(self, word: str) -> str:
        return self.stemmer.stemWord(word.lower())
