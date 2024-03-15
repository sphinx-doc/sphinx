from sphinx.search import SearchLanguage, languages


class NullStemmedLanguage(SearchLanguage):

    def split(self, input: str) -> list[str]:
        return input.split()

    def stem(self, word: str) -> str:
        return word.lower()


languages["xx"] = NullStemmedLanguage
html_search_language = "xx"
