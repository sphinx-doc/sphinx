# -*- coding: utf-8 -*-
"""
    sphinx.search
    ~~~~~~~~~~~~~

    Create a search index for offline search.

    :copyright: 2007 by Armin Ronacher.
    :license: Python license.
"""
import re
import pickle

from collections import defaultdict
from docutils.nodes import Text, NodeVisitor
from .util.stemmer import PorterStemmer
from .util.json import dump_json


word_re = re.compile(r'\w+(?u)')


class Stemmer(PorterStemmer):
    """
    All those porter stemmer implementations look hideous.
    make at least the stem method nicer.
    """

    def stem(self, word):
        return PorterStemmer.stem(self, word, 0, len(word) - 1)


class WordCollector(NodeVisitor):
    """
    A special visitor that collects words for the `IndexBuilder`.
    """

    def __init__(self, document):
        NodeVisitor.__init__(self, document)
        self.found_words = []

    def dispatch_visit(self, node):
        if node.__class__ is Text:
            self.found_words.extend(word_re.findall(node.astext()))


class IndexBuilder(object):
    """
    Helper class that creates a searchindex based on the doctrees
    passed to the `feed` method.
    """
    formats = {
        'json':     dump_json,
        'pickle':   pickle.dumps
    }

    def __init__(self):
        self._filenames = {}
        self._mapping = {}
        self._titles = {}
        self._categories = {}
        self._stemmer = Stemmer()

    def dump(self, stream, format):
        """Dump the freezed index to a stream."""
        stream.write(self.formats[format](self.freeze()))

    def freeze(self):
        """
        Create a useable data structure. You can pass this output
        to the `SearchFrontend` to search the index.
        """
        return [
            [k for k, v in sorted(self._filenames.items(),
                                  key=lambda x: x[1])],
            dict(item for item in sorted(self._categories.items(),
                                         key=lambda x: x[0])),
            [v for k, v in sorted(self._titles.items(),
                                  key=lambda x: x[0])],
            dict(item for item in sorted(self._mapping.items(),
                                         key=lambda x: x[0])),
        ]

    def feed(self, filename, category, title, doctree):
        """Feed a doctree to the index."""
        file_id = self._filenames.setdefault(filename, len(self._filenames))
        self._titles[file_id] = title
        visitor = WordCollector(doctree)
        doctree.walk(visitor)
        self._categories.setdefault(category, set()).add(file_id)
        for word in word_re.findall(title) + visitor.found_words:
            self._mapping.setdefault(self._stemmer.stem(word.lower()),
                                     set()).add(file_id)


class SearchFrontend(object):
    """
    This class acts as a frontend for the search index. It can search
    a searchindex as provided by `IndexBuilder`.
    """

    def __init__(self, index):
        self.filenames, self.areas, self.titles, self.words = index
        self._stemmer = Stemmer()

    def query(self, required, excluded, areas):
        file_map = defaultdict(set)
        for word in required:
            if word not in self.words:
                break
            for fid in self.words[word]:
                file_map[fid].add(word)

        return sorted(((self.filenames[fid], self.titles[fid])
            for fid, words in file_map.iteritems()
            if len(words) == len(required) and
               any(fid in self.areas.get(area, ()) for area in areas) and not
               any(fid in self.words.get(word, ()) for word in excluded)
        ), key=lambda x: x[1].lower())

    def search(self, searchstring, areas):
        required = set()
        excluded = set()
        for word in searchstring.split():
            if word.startswith('-'):
                storage = excluded
                word = word[1:]
            else:
                storage = required
            storage.add(self._stemmer.stem(word.lower()))

        return self.query(required, excluded, areas)
