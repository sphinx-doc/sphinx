"""English search language: includes the JS porter stemmer."""

from __future__ import annotations

import snowballstemmer

from sphinx.search import SearchLanguage
from sphinx.search._stopwords.en import ENGLISH_STOPWORDS


class SearchEnglish(SearchLanguage):
    lang = 'en'
    language_name = 'English'
    js_stemmer_rawcode = 'english-stemmer.js'
    stopwords = ENGLISH_STOPWORDS

    def init(self, options: dict[str, str]) -> None:
        self.stemmer = snowballstemmer.stemmer('english')

    def stem(self, word: str) -> str:
        return self.stemmer.stemWord(word.lower())
