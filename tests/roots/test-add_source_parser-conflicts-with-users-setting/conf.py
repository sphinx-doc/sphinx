# -*- coding: utf-8 -*-

import os
import sys
from docutils.parsers import Parser

sys.path.insert(0, os.path.abspath('.'))


class DummyTestParser(Parser):
    pass


extensions = ['test_source_parser']
source_suffix = ['.rst', '.test']
source_parsers = {
    '.test': DummyTestParser
}
