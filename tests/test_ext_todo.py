# -*- coding: utf-8 -*-
"""
    test_ext_todo
    ~~~~~~~~~~~~~

    Test sphinx.ext.todo extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx('html', testroot='ext-todo', freshenv=True,
                    confoverrides={'todo_include_todos': True, 'todo_emit_warnings': True})
def test_todo(app, status, warning):
    todos = []

    def on_todo_defined(app, node):
        todos.append(node)

    app.connect('todo-defined', on_todo_defined)
    app.builder.build_all()

    # check todolist
    content = (app.outdir / 'index.html').text()
    html = ('<p class="first admonition-title">Todo</p>\n'
            '<p class="last">todo in foo</p>')
    assert re.search(html, content, re.S)

    html = ('<p class="first admonition-title">Todo</p>\n'
            '<p class="last">todo in bar</p>')
    assert re.search(html, content, re.S)

    # check todo
    content = (app.outdir / 'foo.html').text()
    html = ('<p class="first admonition-title">Todo</p>\n'
            '<p class="last">todo in foo</p>')
    assert re.search(html, content, re.S)

    # check emitted warnings
    assert 'WARNING: TODO entry found: todo in foo' in warning.getvalue()
    assert 'WARNING: TODO entry found: todo in bar' in warning.getvalue()

    # check handled event
    assert len(todos) == 2
    assert set(todo[1].astext() for todo in todos) == set(['todo in foo', 'todo in bar'])


@pytest.mark.sphinx('html', testroot='ext-todo', freshenv=True,
                    confoverrides={'todo_include_todos': False, 'todo_emit_warnings': True})
def test_todo_not_included(app, status, warning):
    todos = []

    def on_todo_defined(app, node):
        todos.append(node)

    app.connect('todo-defined', on_todo_defined)
    app.builder.build_all()

    # check todolist
    content = (app.outdir / 'index.html').text()
    html = ('<p class="first admonition-title">Todo</p>\n'
            '<p class="last">todo in foo</p>')
    assert not re.search(html, content, re.S)

    html = ('<p class="first admonition-title">Todo</p>\n'
            '<p class="last">todo in bar</p>')
    assert not re.search(html, content, re.S)

    # check todo
    content = (app.outdir / 'foo.html').text()
    html = ('<p class="first admonition-title">Todo</p>\n'
            '<p class="last">todo in foo</p>')
    assert not re.search(html, content, re.S)

    # check emitted warnings
    assert 'WARNING: TODO entry found: todo in foo' in warning.getvalue()
    assert 'WARNING: TODO entry found: todo in bar' in warning.getvalue()

    # check handled event
    assert len(todos) == 2
    assert set(todo[1].astext() for todo in todos) == set(['todo in foo', 'todo in bar'])


@pytest.mark.sphinx('latex', testroot='ext-todo', freshenv=True,
                    confoverrides={'todo_include_todos': True})
def test_todo_valid_link(app, status, warning):
    """
    Test that the inserted "original entry" links for todo items have a target
    that exists in the LaTeX output. The target was previously incorrectly
    omitted (GitHub issue #1020).
    """

    # Ensure the LaTeX output is built.
    app.builder.build_all()

    content = (app.outdir / 'TodoTests.tex').text()

    # Look for the link to foo. Note that there are two of them because the
    # source document uses todolist twice. We could equally well look for links
    # to bar.
    link = r'\{\\hyperref\[\\detokenize\{(.*?foo.*?)}]\{\\sphinxcrossref{' \
        r'\\sphinxstyleemphasis{original entry}}}}'
    m = re.findall(link, content)
    assert len(m) == 2
    target = m[0]

    # Look for the targets of this link.
    labels = [m for m in re.findall(r'\\label\{([^}]*)}', content) if m == target]

    # If everything is correct we should have exactly one target.
    assert len(labels) == 1
