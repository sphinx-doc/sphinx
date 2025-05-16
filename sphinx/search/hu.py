"""Hungarian search language: includes the JS Hungarian stemmer."""

from __future__ import annotations

import snowballstemmer

from sphinx.search import SearchLanguage
from sphinx.search._stopwords.hu import HUNGARIAN_STOPWORDS


class SearchHungarian(SearchLanguage):
    lang = 'hu'
    language_name = 'Hungarian'
    js_stemmer_rawcode = 'hungarian-stemmer.js'
    stopwords = HUNGARIAN_STOPWORDS

    def init(self, options: dict[str, str]) -> None:
        self.stemmer = snowballstemmer.stemmer('hungarian')

    def stem(self, word: str) -> str:
        return self.stemmer.stemWord(word.lower())
