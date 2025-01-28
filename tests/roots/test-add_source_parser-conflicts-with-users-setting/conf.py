import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

from docutils.parsers import Parser


class DummyTestParser(Parser):
    supported = ('dummy',)


extensions = ['source_parser']
source_suffix = {
    '.rst': 'restructuredtext',
    '.test': 'restructuredtext',
}
source_parsers = {
    '.test': DummyTestParser,
}
