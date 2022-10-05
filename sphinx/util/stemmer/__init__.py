"""Word stemming utilities for Sphinx."""

import warnings

import snowballstemmer

from sphinx.deprecation import RemovedInSphinx70Warning


class PorterStemmer:
    def __init__(self) -> None:
        warnings.warn(f"{self.__class__.__name__} is deprecated, use "
                      "snowballstemmer.stemmer('porter') instead.",
                      RemovedInSphinx70Warning, stacklevel=2)
        self.stemmer = snowballstemmer.stemmer('porter')

    def stem(self, p: str, i: int, j: int) -> str:
        warnings.warn(f"{self.__class__.__name__}.stem() is deprecated, use "
                      "snowballstemmer.stemmer('porter').stemWord() instead.",
                      RemovedInSphinx70Warning, stacklevel=2)
        return self.stemmer.stemWord(p)


class BaseStemmer:
    def __init__(self) -> None:
        warnings.warn(f"{self.__class__.__name__} is deprecated, use "
                      "snowballstemmer.stemmer('porter') instead.",
                      RemovedInSphinx70Warning, stacklevel=3)

    def stem(self, word: str) -> str:
        raise NotImplementedError


class PyStemmer(BaseStemmer):
    def __init__(self) -> None:
        super().__init__()
        self.stemmer = snowballstemmer.stemmer('porter')

    def stem(self, word: str) -> str:
        warnings.warn(f"{self.__class__.__name__}.stem() is deprecated, use "
                      "snowballstemmer.stemmer('porter').stemWord() instead.",
                      RemovedInSphinx70Warning, stacklevel=2)
        return self.stemmer.stemWord(word)


class StandardStemmer(BaseStemmer):
    def __init__(self) -> None:
        super().__init__()
        self.stemmer = snowballstemmer.stemmer('porter')

    def stem(self, word: str) -> str:
        warnings.warn(f"{self.__class__.__name__}.stem() is deprecated, use "
                      "snowballstemmer.stemmer('porter').stemWord() instead.",
                      RemovedInSphinx70Warning, stacklevel=2)
        return self.stemmer.stemWord(word)


def get_stemmer() -> BaseStemmer:
    warnings.warn("get_stemmer() is deprecated, use "
                  "snowballstemmer.stemmer('porter') instead.",
                  RemovedInSphinx70Warning, stacklevel=2)
    return PyStemmer()
