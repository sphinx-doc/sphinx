"""Word stemming utilities for Sphinx."""

from sphinx.util.stemmer.porter import PorterStemmer

try:
    from Stemmer import Stemmer as _PyStemmer
    PYSTEMMER = True
except ImportError:
    PYSTEMMER = False
else:
    _PyStemmer.stem = _PyStemmer.stemWord  # standard .stem() method


class BaseStemmer:
    def stem(self, word: str) -> str:
        raise NotImplementedError


def get_stemmer() -> BaseStemmer:
    if PYSTEMMER:
        return _PyStemmer()  # type: ignore
    return PorterStemmer()  # type: ignore
