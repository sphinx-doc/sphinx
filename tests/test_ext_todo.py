"""
    test_ext_todo
    ~~~~~~~~~~~~~

    Test sphinx.ext.todo extension.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
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
    content = (app.outdir / 'index.html').read_text()
    assert ('<p class="admonition-title">Todo</p>\n'
            '<p>todo in foo</p>') in content

    assert ('<p class="admonition-title">Todo</p>\n'
            '<p>todo in bar</p>') in content

    # check todo
    content = (app.outdir / 'foo.html').read_text()
    assert ('<p class="admonition-title">Todo</p>\n'
            '<p>todo in foo</p>') in content

    assert ('<p class="admonition-title">Todo</p>\n'
            '<p>todo in param field</p>') in content

    # check emitted warnings
    assert 'WARNING: TODO entry found: todo in foo' in warning.getvalue()
    assert 'WARNING: TODO entry found: todo in bar' in warning.getvalue()

    # check handled event
    assert len(todos) == 3
    assert {todo[1].astext() for todo in todos} == {'todo in foo',
                                                    'todo in bar',
                                                    'todo in param field'}


@pytest.mark.sphinx('html', testroot='ext-todo', freshenv=True,
                    confoverrides={'todo_include_todos': False, 'todo_emit_warnings': True})
def test_todo_not_included(app, status, warning):
    todos = []

    def on_todo_defined(app, node):
        todos.append(node)

    app.connect('todo-defined', on_todo_defined)
    app.builder.build_all()

    # check todolist
    content = (app.outdir / 'index.html').read_text()
    assert ('<p class="admonition-title">Todo</p>\n'
            '<p>todo in foo</p>') not in content

    assert ('<p class="admonition-title">Todo</p>\n'
            '<p>todo in bar</p>') not in content

    # check todo
    content = (app.outdir / 'foo.html').read_text()
    assert ('<p class="admonition-title">Todo</p>\n'
            '<p>todo in foo</p>') not in content

    # check emitted warnings
    assert 'WARNING: TODO entry found: todo in foo' in warning.getvalue()
    assert 'WARNING: TODO entry found: todo in bar' in warning.getvalue()

    # check handled event
    assert len(todos) == 3
    assert {todo[1].astext() for todo in todos} == {'todo in foo',
                                                    'todo in bar',
                                                    'todo in param field'}


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

    content = (app.outdir / 'python.tex').read_text()

    # Look for the link to foo. Note that there are two of them because the
    # source document uses todolist twice. We could equally well look for links
    # to bar.
    link = (r'{\\hyperref\[\\detokenize{(.*?foo.*?)}]{\\sphinxcrossref{'
            r'\\sphinxstyleemphasis{original entry}}}}')
    m = re.findall(link, content)
    assert len(m) == 4
    target = m[0]

    # Look for the targets of this link.
    labels = re.findall(r'\\label{\\detokenize{([^}]*)}}', content)
    matched = [l for l in labels if l == target]

    # If everything is correct we should have exactly one target.
    assert len(matched) == 1
