# -*- coding: utf-8 -*-
"""
    test_pycode
    ~~~~~~~~~~~

    Test pycode.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import sys

from six import PY2

import sphinx
from sphinx.pycode import ModuleAnalyzer

SPHINX_MODULE_PATH = os.path.splitext(sphinx.__file__)[0] + '.py'


def test_ModuleAnalyzer_for_string():
    analyzer = ModuleAnalyzer.for_string('print("Hello world")', 'module_name')
    assert analyzer.modname == 'module_name'
    assert analyzer.srcname == '<string>'
    if PY2:
        assert analyzer.encoding == 'ascii'
    else:
        assert analyzer.encoding is None


def test_ModuleAnalyzer_for_file():
    analyzer = ModuleAnalyzer.for_string(SPHINX_MODULE_PATH, 'sphinx')
    assert analyzer.modname == 'sphinx'
    assert analyzer.srcname == '<string>'
    if PY2:
        assert analyzer.encoding == 'ascii'
    else:
        assert analyzer.encoding is None


def test_ModuleAnalyzer_for_module():
    analyzer = ModuleAnalyzer.for_module('sphinx')
    assert analyzer.modname == 'sphinx'
    assert analyzer.srcname in (SPHINX_MODULE_PATH,
                                os.path.abspath(SPHINX_MODULE_PATH))
    assert analyzer.encoding == 'utf-8'


def test_ModuleAnalyzer_for_file_in_egg(rootdir):
    try:
        path = rootdir / 'test-pycode-egg' / 'sample-0.0.0-py3.7.egg'
        sys.path.insert(0, path)

        import sample
        analyzer = ModuleAnalyzer.for_file(sample.__file__, 'sample')
        docs = analyzer.find_attr_docs()
        assert docs == {('', 'CONSTANT'): ['constant on sample.py', '']}
    finally:
        sys.path.pop(0)


def test_ModuleAnalyzer_for_module_in_egg(rootdir):
    try:
        path = rootdir / 'test-pycode-egg' / 'sample-0.0.0-py3.7.egg'
        sys.path.insert(0, path)

        analyzer = ModuleAnalyzer.for_module('sample')
        docs = analyzer.find_attr_docs()
        assert docs == {('', 'CONSTANT'): ['constant on sample.py', '']}
    finally:
        sys.path.pop(0)


def test_ModuleAnalyzer_find_tags():
    code = ('class Foo(object):\n'  # line: 1
            '    """class Foo!"""\n'
            '    def __init__(self):\n'
            '       pass\n'
            '\n'
            '    def bar(self, arg1, arg2=True, *args, **kwargs):\n'
            '       """method Foo.bar"""\n'
            '       pass\n'
            '\n'
            '    class Baz(object):\n'
            '       def __init__(self):\n'  # line: 11
            '           pass\n'
            '\n'
            'def qux():\n'
            '   """function baz"""\n'
            '   pass\n'
            '\n'
            '@decorator1\n'
            '@decorator2\n'
            'def quux():\n'
            '   pass\n'  # line: 21
            '\n'
            'class Corge(object):\n'
            '    @decorator1\n'
            '    @decorator2\n'
            '    def grault(self):\n'
            '        pass\n')
    analyzer = ModuleAnalyzer.for_string(code, 'module')
    tags = analyzer.find_tags()
    assert set(tags.keys()) == {'Foo', 'Foo.__init__', 'Foo.bar',
                                'Foo.Baz', 'Foo.Baz.__init__', 'qux', 'quux',
                                'Corge', 'Corge.grault'}
    assert tags['Foo'] == ('class', 1, 12)  # type, start, end
    assert tags['Foo.__init__'] == ('def', 3, 4)
    assert tags['Foo.bar'] == ('def', 6, 8)
    assert tags['Foo.Baz'] == ('class', 10, 12)
    assert tags['Foo.Baz.__init__'] == ('def', 11, 12)
    assert tags['qux'] == ('def', 14, 16)
    assert tags['quux'] == ('def', 18, 21)
    assert tags['Corge'] == ('class', 23, 27)
    assert tags['Corge.grault'] == ('def', 24, 27)


def test_ModuleAnalyzer_find_attr_docs():
    code = ('class Foo(object):\n'
            '    """class Foo!"""\n'
            '    #: comment before attr1\n'
            '    attr1 = None\n'
            '    attr2 = None  # attribute comment for attr2 (without colon)\n'
            '    attr3 = None  #: attribute comment for attr3\n'
            '    attr4 = None  #: long attribute comment\n'
            '                  #: for attr4\n'
            '    #: comment before attr5\n'
            '    attr5 = None  #: attribute comment for attr5\n'
            '    attr6, attr7 = 1, 2  #: this comment is ignored\n'
            '\n'
            '    def __init__(self):\n'
            '       self.attr8 = None  #: first attribute comment (ignored)\n'
            '       self.attr8 = None  #: attribute comment for attr8\n'
            '       #: comment before attr9\n'
            '       self.attr9 = None  #: comment after attr9\n'
            '       "string after attr9"\n'
            '\n'
            '    def bar(self, arg1, arg2=True, *args, **kwargs):\n'
            '       """method Foo.bar"""\n'
            '       pass\n'
            '\n'
            'def baz():\n'
            '   """function baz"""\n'
            '   pass\n'
            '\n'
            'class Qux: attr1 = 1; attr2 = 2')
    analyzer = ModuleAnalyzer.for_string(code, 'module')
    docs = analyzer.find_attr_docs()
    assert set(docs) == {('Foo', 'attr1'),
                         ('Foo', 'attr3'),
                         ('Foo', 'attr4'),
                         ('Foo', 'attr5'),
                         ('Foo', 'attr6'),
                         ('Foo', 'attr7'),
                         ('Foo', 'attr8'),
                         ('Foo', 'attr9')}
    assert docs[('Foo', 'attr1')] == ['comment before attr1', '']
    assert docs[('Foo', 'attr3')] == ['attribute comment for attr3', '']
    assert docs[('Foo', 'attr4')] == ['long attribute comment', '']
    assert docs[('Foo', 'attr4')] == ['long attribute comment', '']
    assert docs[('Foo', 'attr5')] == ['attribute comment for attr5', '']
    assert docs[('Foo', 'attr6')] == ['this comment is ignored', '']
    assert docs[('Foo', 'attr7')] == ['this comment is ignored', '']
    assert docs[('Foo', 'attr8')] == ['attribute comment for attr8', '']
    assert docs[('Foo', 'attr9')] == ['string after attr9', '']
    assert analyzer.tagorder == {'Foo': 0,
                                 'Foo.__init__': 8,
                                 'Foo.attr1': 1,
                                 'Foo.attr2': 2,
                                 'Foo.attr3': 3,
                                 'Foo.attr4': 4,
                                 'Foo.attr5': 5,
                                 'Foo.attr6': 6,
                                 'Foo.attr7': 7,
                                 'Foo.attr8': 10,
                                 'Foo.attr9': 12,
                                 'Foo.bar': 13,
                                 'baz': 14,
                                 'Qux': 15,
                                 'Qux.attr1': 16,
                                 'Qux.attr2': 17}
