"""Portuguese search language: includes the JS Portuguese stemmer."""

from __future__ import annotations

import snowballstemmer

from sphinx.search import SearchLanguage
from sphinx.search._stopwords.pt import PORTUGUESE_STOPWORDS


class SearchPortuguese(SearchLanguage):
    lang = 'pt'
    language_name = 'Portuguese'
    js_stemmer_rawcode = 'portuguese-stemmer.js'
    stopwords = PORTUGUESE_STOPWORDS

    def init(self, options: dict[str, str]) -> None:
        self.stemmer = snowballstemmer.stemmer('portuguese')

    def stem(self, word: str) -> str:
        return self.stemmer.stemWord(word.lower())
