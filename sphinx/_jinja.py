# -*- coding: utf-8 -*-
"""
    sphinx._jinja
    ~~~~~~~~~~~~~

    Jinja glue.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import sys
import codecs
from os import path

sys.path.insert(0, path.dirname(__file__))

from jinja import Environment
from jinja.loaders import BaseLoader
from jinja.exceptions import TemplateNotFound

class SphinxFileSystemLoader(BaseLoader):
    """
    A loader that loads templates either relative to one of a list of given
    paths, or from an absolute path.
    """

    def __init__(self, basepath, extpaths):
        self.basepath = path.abspath(basepath)
        self.extpaths = map(path.abspath, extpaths)
        self.searchpaths = self.extpaths + [self.basepath]

    def get_source(self, environment, name, parent):
        name = name.replace('/', path.sep)
        if name.startswith('!'):
            name = name[1:]
            if not path.exists(path.join(self.basepath, name)):
                raise TemplateNotFound(name)
            filename = path.join(self.basepath, name)
        elif path.isabs(name):
            if not path.exists(name):
                raise TemplateNotFound(name)
            filename = name
        else:
            for searchpath in self.searchpaths:
                if path.exists(path.join(searchpath, name)):
                    filename = path.join(searchpath, name)
                    break
            else:
                raise TemplateNotFound(name)
        f = codecs.open(filename, 'r', environment.template_charset)
        try:
            return f.read()
        finally:
            f.close()
