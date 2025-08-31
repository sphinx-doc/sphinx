"""Tests sphinx.util.rst functions."""

from __future__ import annotations

from docutils.statemachine import StringList
from jinja2 import Environment

from sphinx.util.rst import (
    _append_epilogue,
    _prepend_prologue,
    escape,
    heading,
    textwidth,
)


def test_escape() -> None:
    assert escape(':ref:`id`') == r'\:ref\:\`id\`'
    assert escape('footnote [#]_') == r'footnote \[\#\]\_'
    assert escape('sphinx.application') == r'sphinx.application'
    assert escape('.. toctree::') == r'\.. toctree\:\:'


def test_append_epilogue() -> None:
    epilog = 'this is rst_epilog\ngood-bye reST!'
    content = StringList(
        ['hello Sphinx world', 'Sphinx is a document generator'],
        'dummy.rst',
    )
    _append_epilogue(content, epilog)

    assert list(content.xitems()) == [
        ('dummy.rst', 0, 'hello Sphinx world'),
        ('dummy.rst', 1, 'Sphinx is a document generator'),
        ('dummy.rst', 2, ''),
        ('<rst_epilogue>', 0, 'this is rst_epilog'),
        ('<rst_epilogue>', 1, 'good-bye reST!'),
    ]


def test_prepend_prologue() -> None:
    prologue = 'this is rst_prolog\nhello reST!'
    content = StringList(
        [
            ':title: test of SphinxFileInput',
            ':author: Sphinx team',
            '',
            'hello Sphinx world',
            'Sphinx is a document generator',
        ],
        'dummy.rst',
    )
    _prepend_prologue(content, prologue)

    assert list(content.xitems()) == [
        ('dummy.rst', 0, ':title: test of SphinxFileInput'),
        ('dummy.rst', 1, ':author: Sphinx team'),
        ('<generated>', 0, ''),
        ('<rst_prologue>', 0, 'this is rst_prolog'),
        ('<rst_prologue>', 1, 'hello reST!'),
        ('<generated>', 0, ''),
        ('dummy.rst', 2, ''),
        ('dummy.rst', 3, 'hello Sphinx world'),
        ('dummy.rst', 4, 'Sphinx is a document generator'),
    ]


def test_prepend_prolog_with_CR() -> None:
    # prologue having CR at tail
    prologue = 'this is rst_prolog\nhello reST!\n'
    content = StringList(
        ['hello Sphinx world', 'Sphinx is a document generator'],
        'dummy.rst',
    )
    _prepend_prologue(content, prologue)

    assert list(content.xitems()) == [
        ('<rst_prologue>', 0, 'this is rst_prolog'),
        ('<rst_prologue>', 1, 'hello reST!'),
        ('<generated>', 0, ''),
        ('dummy.rst', 0, 'hello Sphinx world'),
        ('dummy.rst', 1, 'Sphinx is a document generator'),
    ]


def test_prepend_prolog_without_CR() -> None:
    # prologue not having CR at tail
    prologue = 'this is rst_prolog\nhello reST!'
    content = StringList(
        ['hello Sphinx world', 'Sphinx is a document generator'],
        'dummy.rst',
    )
    _prepend_prologue(content, prologue)

    assert list(content.xitems()) == [
        ('<rst_prologue>', 0, 'this is rst_prolog'),
        ('<rst_prologue>', 1, 'hello reST!'),
        ('<generated>', 0, ''),
        ('dummy.rst', 0, 'hello Sphinx world'),
        ('dummy.rst', 1, 'Sphinx is a document generator'),
    ]


def test_prepend_prolog_with_roles_in_sections() -> None:
    prologue = 'this is rst_prolog\nhello reST!'
    content = StringList(
        [
            ':title: test of SphinxFileInput',
            ':author: Sphinx team',
            '',  # this newline is required
            ':mod:`foo`',
            '----------',
            '',
            'hello',
        ],
        'dummy.rst',
    )
    _prepend_prologue(content, prologue)

    assert list(content.xitems()) == [
        ('dummy.rst', 0, ':title: test of SphinxFileInput'),
        ('dummy.rst', 1, ':author: Sphinx team'),
        ('<generated>', 0, ''),
        ('<rst_prologue>', 0, 'this is rst_prolog'),
        ('<rst_prologue>', 1, 'hello reST!'),
        ('<generated>', 0, ''),
        ('dummy.rst', 2, ''),
        ('dummy.rst', 3, ':mod:`foo`'),
        ('dummy.rst', 4, '----------'),
        ('dummy.rst', 5, ''),
        ('dummy.rst', 6, 'hello'),
    ]


def test_prepend_prolog_with_roles_in_sections_with_newline() -> None:
    # prologue with trailing line break
    prologue = 'this is rst_prolog\nhello reST!\n'
    content = StringList([':mod:`foo`', '-' * 10, '', 'hello'], 'dummy.rst')
    _prepend_prologue(content, prologue)

    assert list(content.xitems()) == [
        ('<rst_prologue>', 0, 'this is rst_prolog'),
        ('<rst_prologue>', 1, 'hello reST!'),
        ('<generated>', 0, ''),
        ('dummy.rst', 0, ':mod:`foo`'),
        ('dummy.rst', 1, '----------'),
        ('dummy.rst', 2, ''),
        ('dummy.rst', 3, 'hello'),
    ]


def test_prepend_prolog_with_roles_in_sections_without_newline() -> None:
    # prologue with no trailing line break
    prologue = 'this is rst_prolog\nhello reST!'
    content = StringList([':mod:`foo`', '-' * 10, '', 'hello'], 'dummy.rst')
    _prepend_prologue(content, prologue)

    assert list(content.xitems()) == [
        ('<rst_prologue>', 0, 'this is rst_prolog'),
        ('<rst_prologue>', 1, 'hello reST!'),
        ('<generated>', 0, ''),
        ('dummy.rst', 0, ':mod:`foo`'),
        ('dummy.rst', 1, '----------'),
        ('dummy.rst', 2, ''),
        ('dummy.rst', 3, 'hello'),
    ]


def test_textwidth() -> None:
    assert textwidth('Hello') == 5
    assert textwidth('русский язык') == 12
    assert textwidth('русский язык', 'WFA') == 23  # Cyrillic are ambiguous chars


def test_heading() -> None:
    env = Environment(autoescape=True)
    env.extend(language=None)

    assert heading(env, 'Hello') == 'Hello\n====='
    assert heading(env, 'Hello', 1) == 'Hello\n====='
    assert heading(env, 'Hello', 2) == 'Hello\n-----'
    assert heading(env, 'Hello', 3) == 'Hello\n~~~~~'
    assert heading(env, 'русский язык', 1) == 'русский язык\n============'

    # language=ja: ambiguous
    env.language = 'ja'  # type: ignore[attr-defined]
    assert heading(env, 'русский язык', 1) == 'русский язык\n======================='
