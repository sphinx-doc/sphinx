"""
    test_pycode_parser
    ~~~~~~~~~~~~~~~~~~

    Test pycode.parser.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.pycode.parser import Parser
from sphinx.util.inspect import signature_from_str


def test_comment_picker_basic():
    source = ('a = 1 + 1      #: assignment\n'
              'b = 1 +\\\n 1  #: assignment including a CR\n'
              'c = (1 +\n 1)  #: tuple  \n'
              'd = {1, \n 1}  #:     set\n'
              'e = [1, \n 1]  #: list #: additional comment\n'
              'f = "abc"\n'
              '#: string; comment on next line (ignored)\n'
              'g = 1.0\n'
              '"""float; string on next line"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'assignment',
                               ('', 'b'): 'assignment including a CR',
                               ('', 'c'): 'tuple  ',
                               ('', 'd'): '    set',
                               ('', 'e'): 'list #: additional comment',
                               ('', 'g'): 'float; string on next line'}


def test_comment_picker_location():
    # multiple "before" comments
    source = ('#: comment before assignment1\n'
              '#:\n'
              '#: comment before assignment2\n'
              'a = 1 + 1\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): ('comment before assignment1\n'
                                           '\n'
                                           'comment before assignment2')}

    # before and after comments
    source = ('#: comment before assignment\n'
              'a = 1 + 1  #: comment after assignment\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'comment after assignment'}

    # after comment and next line string
    source = ('a = 1 + 1\n  #: comment after assignment\n'
              '"""string on next line"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'string on next line'}

    # before comment and next line string
    source = ('#: comment before assignment\n'
              'a = 1 + 1\n'
              '"""string on next line"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'string on next line'}

    # before comment, after comment and next line string
    source = ('#: comment before assignment\n'
              'a = 1 + 1  #: comment after assignment\n'
              '"""string on next line"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'string on next line'}

    # inside __init__ method
    source = ('class Foo(object):\n'
              '    def __init__(self):\n'
              '        #: comment before assignment\n'
              '        self.attr1 = None\n'
              '        self.attr2 = None  #: comment after assignment\n'
              '\n'
              '        #: comment for attr3(1)\n'
              '        self.attr3 = None  #: comment for attr3(2)\n'
              '        """comment for attr3(3)"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('Foo', 'attr1'): 'comment before assignment',
                               ('Foo', 'attr2'): 'comment after assignment',
                               ('Foo', 'attr3'): 'comment for attr3(3)'}


def test_annotated_assignment():
    source = ('a: str = "Sphinx"  #: comment\n'
              'b: int = 1\n'
              '"""string on next line"""\n'
              'c: int  #: comment\n'
              'd = 1  # type: int\n'
              '"""string on next line"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'comment',
                               ('', 'b'): 'string on next line',
                               ('', 'c'): 'comment',
                               ('', 'd'): 'string on next line'}
    assert parser.annotations == {('', 'a'): 'str',
                                  ('', 'b'): 'int',
                                  ('', 'c'): 'int',
                                  ('', 'd'): 'int'}
    assert parser.definitions == {}


def test_complex_assignment():
    source = ('a = 1 + 1; b = a  #: compound statement\n'
              'c, d = (1, 1)  #: unpack assignment\n'
              'e = True  #: first assignment\n'
              'e = False  #: second assignment\n'
              'f = g = None  #: multiple assignment at once\n'
              '(theta, phi) = (0, 0.5)  #: unpack assignment via tuple\n'
              '[x, y] = (5, 6)  #: unpack assignment via list\n'
              )
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'b'): 'compound statement',
                               ('', 'c'): 'unpack assignment',
                               ('', 'd'): 'unpack assignment',
                               ('', 'e'): 'second assignment',
                               ('', 'f'): 'multiple assignment at once',
                               ('', 'g'): 'multiple assignment at once',
                               ('', 'theta'): 'unpack assignment via tuple',
                               ('', 'phi'): 'unpack assignment via tuple',
                               ('', 'x'): 'unpack assignment via list',
                               ('', 'y'): 'unpack assignment via list',
                               }
    assert parser.definitions == {}


def test_complex_assignment_py3():
    source = ('a, *b, c = (1, 2, 3, 4)  #: unpack assignment\n'
              'd, *self.attr = (5, 6, 7)  #: unpack assignment2\n'
              'e, *f[0] = (8, 9, 0)  #: unpack assignment3\n'
              )
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'unpack assignment',
                               ('', 'b'): 'unpack assignment',
                               ('', 'c'): 'unpack assignment',
                               ('', 'd'): 'unpack assignment2',
                               ('', 'e'): 'unpack assignment3',
                               }
    assert parser.definitions == {}


def test_assignment_in_try_clause():
    source = ('try:\n'
              '    a = None  #: comment\n'
              'except:\n'
              '    b = None  #: ignored\n'
              'else:\n'
              '    c = None  #: comment\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'a'): 'comment',
                               ('', 'c'): 'comment'}
    assert parser.deforders == {'a': 0,
                                'c': 1}


def test_obj_assignment():
    source = ('obj = SomeObject()  #: some object\n'
              'obj.attr = 1  #: attr1\n'
              'obj.attr.attr = 1  #: attr2\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'obj'): 'some object'}
    assert parser.definitions == {}


def test_container_assignment():
    source = ('l = []  #: list\n'
              'l[1] = True  #: list assignment\n'
              'l[0:0] = []  #: list assignment\n'
              'l[_from:_to] = []  #: list assignment\n'
              'd = {}  #: dict\n'
              'd["doc"] = 1  #: dict assignment\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('', 'l'): 'list',
                               ('', 'd'): 'dict'}
    assert parser.definitions == {}


def test_function():
    source = ('def some_function():\n'
              '    """docstring"""\n'
              '    a = 1 + 1  #: comment1\n'
              '\n'
              '    b = a  #: comment2\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {}
    assert parser.definitions == {'some_function': ('def', 1, 5)}
    assert parser.deforders == {'some_function': 0}


def test_nested_function():
    source = ('def some_function():\n'
              '    a = 1 + 1  #: comment1\n'
              '\n'
              '    def inner_function():\n'
              '        b = 1 + 1  #: comment2\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {}
    assert parser.definitions == {'some_function': ('def', 1, 5)}
    assert parser.deforders == {'some_function': 0}


def test_class():
    source = ('class Foo(object):\n'
              '    attr1 = None  #: comment1\n'
              '    attr2 = None  #: comment2\n'
              '\n'
              '    def __init__(self):\n'
              '        self.a = 1 + 1  #: comment3\n'
              '        self.attr2 = 1 + 1  #: overridden\n'
              '        b = 1 + 1  #: comment5\n'
              '\n'
              '    def some_method(self):\n'
              '        c = 1 + 1  #: comment6\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('Foo', 'attr1'): 'comment1',
                               ('Foo', 'a'): 'comment3',
                               ('Foo', 'attr2'): 'overridden'}
    assert parser.definitions == {'Foo': ('class', 1, 11),
                                  'Foo.__init__': ('def', 5, 8),
                                  'Foo.some_method': ('def', 10, 11)}
    assert parser.deforders == {'Foo': 0,
                                'Foo.attr1': 1,
                                'Foo.__init__': 3,
                                'Foo.a': 4,
                                'Foo.attr2': 5,
                                'Foo.some_method': 6}


def test_class_uses_non_self():
    source = ('class Foo(object):\n'
              '    def __init__(this):\n'
              '        this.a = 1 + 1  #: comment\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('Foo', 'a'): 'comment'}
    assert parser.definitions == {'Foo': ('class', 1, 3),
                                  'Foo.__init__': ('def', 2, 3)}
    assert parser.deforders == {'Foo': 0,
                                'Foo.__init__': 1,
                                'Foo.a': 2}


def test_nested_class():
    source = ('class Foo(object):\n'
              '    attr1 = None  #: comment1\n'
              '\n'
              '    class Bar(object):\n'
              '        attr2 = None  #: comment2\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('Foo', 'attr1'): 'comment1',
                               ('Foo.Bar', 'attr2'): 'comment2'}
    assert parser.definitions == {'Foo': ('class', 1, 5),
                                  'Foo.Bar': ('class', 4, 5)}
    assert parser.deforders == {'Foo': 0,
                                'Foo.attr1': 1,
                                'Foo.Bar': 2,
                                'Foo.Bar.attr2': 3}


def test_class_comment():
    source = ('import logging\n'
              'logger = logging.getLogger(__name__)\n'
              '\n'
              'class Foo(object):\n'
              '    """Bar"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {}
    assert parser.definitions == {'Foo': ('class', 4, 5)}


def test_comment_picker_multiline_string():
    source = ('class Foo(object):\n'
              '    a = None\n'
              '    """multiline\n'
              '    docstring\n'
              '    """\n'
              '    b = None\n'
              '    """\n'
              '    docstring\n'
              '    starts with::\n'
              '\n'
              '        empty line"""\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('Foo', 'a'): 'multiline\ndocstring',
                               ('Foo', 'b'): 'docstring\nstarts with::\n\n    empty line'}


def test_decorators():
    source = ('@deco\n'
              'def func1(): pass\n'
              '\n'
              '@deco(param1, param2)\n'
              'def func2(): pass\n'
              '\n'
              '@deco1\n'
              '@deco2\n'
              'def func3(): pass\n'
              '\n'
              '@deco\n'
              'class Foo():\n'
              '    @deco1\n'
              '    @deco2\n'
              '    def method(self): pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.definitions == {'func1': ('def', 1, 2),
                                  'func2': ('def', 4, 5),
                                  'func3': ('def', 7, 9),
                                  'Foo': ('class', 11, 15),
                                  'Foo.method': ('def', 13, 15)}


def test_async_function_and_method():
    source = ('async def some_function():\n'
              '    """docstring"""\n'
              '    a = 1 + 1  #: comment1\n'
              '\n'
              'class Foo:\n'
              '    async def method(self):\n'
              '        pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.definitions == {'some_function': ('def', 1, 3),
                                  'Foo': ('class', 5, 7),
                                  'Foo.method': ('def', 6, 7)}


def test_imports():
    source = ('import sys\n'
              'from os import environment, path\n'
              '\n'
              'import sphinx as Sphinx\n'
              'from sphinx.application import Sphinx as App\n')
    parser = Parser(source)
    parser.parse()
    assert parser.definitions == {}
    assert parser.deforders == {'sys': 0,
                                'environment': 1,
                                'path': 2,
                                'Sphinx': 3,
                                'App': 4}


def test_formfeed_char():
    source = ('class Foo:\n'
              '\f\n'
              '    attr = 1234  #: comment\n')
    parser = Parser(source)
    parser.parse()
    assert parser.comments == {('Foo', 'attr'): 'comment'}


def test_typing_final():
    source = ('import typing\n'
              '\n'
              '@typing.final\n'
              'def func(): pass\n'
              '\n'
              '@typing.final\n'
              'class Foo:\n'
              '    @typing.final\n'
              '    def meth(self):\n'
              '        pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.finals == ['func', 'Foo', 'Foo.meth']


def test_typing_final_from_import():
    source = ('from typing import final\n'
              '\n'
              '@final\n'
              'def func(): pass\n'
              '\n'
              '@final\n'
              'class Foo:\n'
              '    @final\n'
              '    def meth(self):\n'
              '        pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.finals == ['func', 'Foo', 'Foo.meth']


def test_typing_final_import_as():
    source = ('import typing as foo\n'
              '\n'
              '@foo.final\n'
              'def func(): pass\n'
              '\n'
              '@foo.final\n'
              'class Foo:\n'
              '    @typing.final\n'
              '    def meth(self):\n'
              '        pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.finals == ['func', 'Foo']


def test_typing_final_from_import_as():
    source = ('from typing import final as bar\n'
              '\n'
              '@bar\n'
              'def func(): pass\n'
              '\n'
              '@bar\n'
              'class Foo:\n'
              '    @final\n'
              '    def meth(self):\n'
              '        pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.finals == ['func', 'Foo']


def test_typing_final_not_imported():
    source = ('@typing.final\n'
              'def func(): pass\n'
              '\n'
              '@typing.final\n'
              'class Foo:\n'
              '    @final\n'
              '    def meth(self):\n'
              '        pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.finals == []


def test_typing_overload():
    source = ('import typing\n'
              '\n'
              '@typing.overload\n'
              'def func(x: int, y: int) -> int: pass\n'
              '\n'
              '@typing.overload\n'
              'def func(x: str, y: str) -> str: pass\n'
              '\n'
              'def func(x, y): pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.overloads == {'func': [signature_from_str('(x: int, y: int) -> int'),
                                         signature_from_str('(x: str, y: str) -> str')]}


def test_typing_overload_from_import():
    source = ('from typing import overload\n'
              '\n'
              '@overload\n'
              'def func(x: int, y: int) -> int: pass\n'
              '\n'
              '@overload\n'
              'def func(x: str, y: str) -> str: pass\n'
              '\n'
              'def func(x, y): pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.overloads == {'func': [signature_from_str('(x: int, y: int) -> int'),
                                         signature_from_str('(x: str, y: str) -> str')]}


def test_typing_overload_import_as():
    source = ('import typing as foo\n'
              '\n'
              '@foo.overload\n'
              'def func(x: int, y: int) -> int: pass\n'
              '\n'
              '@foo.overload\n'
              'def func(x: str, y: str) -> str: pass\n'
              '\n'
              'def func(x, y): pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.overloads == {'func': [signature_from_str('(x: int, y: int) -> int'),
                                         signature_from_str('(x: str, y: str) -> str')]}


def test_typing_overload_from_import_as():
    source = ('from typing import overload as bar\n'
              '\n'
              '@bar\n'
              'def func(x: int, y: int) -> int: pass\n'
              '\n'
              '@bar\n'
              'def func(x: str, y: str) -> str: pass\n'
              '\n'
              'def func(x, y): pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.overloads == {'func': [signature_from_str('(x: int, y: int) -> int'),
                                         signature_from_str('(x: str, y: str) -> str')]}


def test_typing_overload_not_imported():
    source = ('@typing.final\n'
              'def func(x: int, y: int) -> int: pass\n'
              '\n'
              '@typing.final\n'
              'def func(x: str, y: str) -> str: pass\n'
              '\n'
              'def func(x, y): pass\n')
    parser = Parser(source)
    parser.parse()
    assert parser.overloads == {}
