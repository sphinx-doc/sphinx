"""Word stemming utilities for Sphinx."""

import snowballstemmer

from sphinx.util.stemmer.porter import PorterStemmer


class BaseStemmer:
    def stem(self, word: str) -> str:
        raise NotImplementedError


def get_stemmer() -> BaseStemmer:
    stemmer = snowballstemmer.stemmer('english')


