"""
    test_util_rst
    ~~~~~~~~~~~~~~~

    Tests sphinx.util.rst functions.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils.statemachine import StringList
from jinja2 import Environment

from sphinx.util.rst import append_epilog, escape, heading, prepend_prolog, textwidth


def test_escape():
    assert escape(':ref:`id`') == r'\:ref\:\`id\`'
    assert escape('footnote [#]_') == r'footnote \[\#\]\_'
    assert escape('sphinx.application') == r'sphinx.application'
    assert escape('.. toctree::') == r'\.. toctree\:\:'


def test_append_epilog(app):
    epilog = 'this is rst_epilog\ngood-bye reST!'
    content = StringList(['hello Sphinx world',
                          'Sphinx is a document generator'],
                         'dummy.rst')
    append_epilog(content, epilog)

    assert list(content.xitems()) == [('dummy.rst', 0, 'hello Sphinx world'),
                                      ('dummy.rst', 1, 'Sphinx is a document generator'),
                                      ('dummy.rst', 2, ''),
                                      ('<rst_epilog>', 0, 'this is rst_epilog'),
                                      ('<rst_epilog>', 1, 'good-bye reST!')]


def test_prepend_prolog(app):
    prolog = 'this is rst_prolog\nhello reST!'
    content = StringList([':title: test of SphinxFileInput',
                          ':author: Sphinx team',
                          '',
                          'hello Sphinx world',
                          'Sphinx is a document generator'],
                         'dummy.rst')
    prepend_prolog(content, prolog)

    assert list(content.xitems()) == [('dummy.rst', 0, ':title: test of SphinxFileInput'),
                                      ('dummy.rst', 1, ':author: Sphinx team'),
                                      ('<generated>', 0, ''),
                                      ('<rst_prolog>', 0, 'this is rst_prolog'),
                                      ('<rst_prolog>', 1, 'hello reST!'),
                                      ('<generated>', 0, ''),
                                      ('dummy.rst', 2, ''),
                                      ('dummy.rst', 3, 'hello Sphinx world'),
                                      ('dummy.rst', 4, 'Sphinx is a document generator')]


def test_prepend_prolog_with_CR(app):
    # prolog having CR at tail
    prolog = 'this is rst_prolog\nhello reST!\n'
    content = StringList(['hello Sphinx world',
                          'Sphinx is a document generator'],
                         'dummy.rst')
    prepend_prolog(content, prolog)

    assert list(content.xitems()) == [('<rst_prolog>', 0, 'this is rst_prolog'),
                                      ('<rst_prolog>', 1, 'hello reST!'),
                                      ('<generated>', 0, ''),
                                      ('dummy.rst', 0, 'hello Sphinx world'),
                                      ('dummy.rst', 1, 'Sphinx is a document generator')]


def test_prepend_prolog_without_CR(app):
    # prolog not having CR at tail
    prolog = 'this is rst_prolog\nhello reST!'
    content = StringList(['hello Sphinx world',
                          'Sphinx is a document generator'],
                         'dummy.rst')
    prepend_prolog(content, prolog)

    assert list(content.xitems()) == [('<rst_prolog>', 0, 'this is rst_prolog'),
                                      ('<rst_prolog>', 1, 'hello reST!'),
                                      ('<generated>', 0, ''),
                                      ('dummy.rst', 0, 'hello Sphinx world'),
                                      ('dummy.rst', 1, 'Sphinx is a document generator')]


def test_textwidth():
    assert textwidth('Hello') == 5
    assert textwidth('русский язык') == 12
    assert textwidth('русский язык', 'WFA') == 23  # Cyrillic are ambiguous chars


def test_heading():
    env = Environment()
    env.extend(language=None)

    assert heading(env, 'Hello') == ('Hello\n'
                                     '=====')
    assert heading(env, 'Hello', 1) == ('Hello\n'
                                        '=====')
    assert heading(env, 'Hello', 2) == ('Hello\n'
                                        '-----')
    assert heading(env, 'Hello', 3) == ('Hello\n'
                                        '~~~~~')
    assert heading(env, 'русский язык', 1) == (
        'русский язык\n'
        '============'
    )

    # language=ja: ambiguous
    env.language = 'ja'
    assert heading(env, 'русский язык', 1) == (
        'русский язык\n'
        '======================='
    )
