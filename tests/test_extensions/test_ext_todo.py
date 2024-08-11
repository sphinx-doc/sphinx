"""Test sphinx.ext.todo extension."""

import re

import pytest


@pytest.mark.sphinx(
    'html',
    testroot='ext-todo',
    freshenv=True,
    confoverrides={'todo_include_todos': True, 'todo_emit_warnings': True},
)
def test_todo(app):
    todos = []

    def on_todo_defined(app, node):
        todos.append(node)

    app.connect('todo-defined', on_todo_defined)
    app.build(force_all=True)

    # check todolist
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p class="admonition-title">Todo</p>\n<p>todo in foo</p>' in content

    assert '<p class="admonition-title">Todo</p>\n<p>todo in bar</p>' in content

    # check todo
    content = (app.outdir / 'foo.html').read_text(encoding='utf8')
    assert '<p class="admonition-title">Todo</p>\n<p>todo in foo</p>' in content

    assert (
        '<p class="admonition-title">Todo</p>\n<p>todo in param field</p>'
    ) in content

    # check emitted warnings
    assert 'WARNING: TODO entry found: todo in foo' in app.warning.getvalue()
    assert 'WARNING: TODO entry found: todo in bar' in app.warning.getvalue()

    # check handled event
    assert len(todos) == 3
    assert {todo[1].astext() for todo in todos} == {
        'todo in foo',
        'todo in bar',
        'todo in param field',
    }


@pytest.mark.sphinx(
    'html',
    testroot='ext-todo',
    freshenv=True,
    confoverrides={'todo_include_todos': False, 'todo_emit_warnings': True},
)
def test_todo_not_included(app):
    todos = []

    def on_todo_defined(app, node):
        todos.append(node)

    app.connect('todo-defined', on_todo_defined)
    app.build(force_all=True)

    # check todolist
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p class="admonition-title">Todo</p>\n<p>todo in foo</p>' not in content

    assert '<p class="admonition-title">Todo</p>\n<p>todo in bar</p>' not in content

    # check todo
    content = (app.outdir / 'foo.html').read_text(encoding='utf8')
    assert '<p class="admonition-title">Todo</p>\n<p>todo in foo</p>' not in content

    # check emitted warnings
    assert 'WARNING: TODO entry found: todo in foo' in app.warning.getvalue()
    assert 'WARNING: TODO entry found: todo in bar' in app.warning.getvalue()

    # check handled event
    assert len(todos) == 3
    assert {todo[1].astext() for todo in todos} == {
        'todo in foo',
        'todo in bar',
        'todo in param field',
    }


@pytest.mark.sphinx(
    'latex',
    testroot='ext-todo',
    freshenv=True,
    confoverrides={'todo_include_todos': True},
)
def test_todo_valid_link(app):
    """
    Test that the inserted "original entry" links for todo items have a target
    that exists in the LaTeX output. The target was previously incorrectly
    omitted (GitHub issue #1020).
    """
    # Ensure the LaTeX output is built.
    app.build(force_all=True)

    content = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')

    # Look for the link to foo. Note that there are two of them because the
    # source document uses todolist twice. We could equally well look for links
    # to bar.
    link = (
        r'{\\hyperref\[\\detokenize{(.*?foo.*?)}]{\\sphinxcrossref{'
        r'\\sphinxstyleemphasis{original entry}}}}'
    )
    m = re.findall(link, content)
    assert len(m) == 4
    target = m[0]

    # Look for the targets of this link.
    labels = re.findall(r'\\label{\\detokenize{([^}]*)}}', content)
    matched = [l for l in labels if l == target]

    # If everything is correct we should have exactly one target.
    assert len(matched) == 1
