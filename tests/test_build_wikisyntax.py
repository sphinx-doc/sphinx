# -*- coding: utf-8 -*-
"""
    test_build_wikisyntax
    ~~~~~~~~~~~~~~~

    Test the build process with Wikisyntax builder with the test root.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app


def with_wikisyntax_app(*args, **kw):
    default_kw = {
        'buildername': 'wikisyntax',
        'testroot': 'build-wikisyntax',
    }
    default_kw.update(kw)
    return with_app(*args, **default_kw)


@with_wikisyntax_app()
def test_ul(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'ul.wiki').text(encoding='utf-8'))

    expected = '\n'.join([
        'Unordered List:',
        '',
        '* item 1',
        '',
        '* item 2',
        '',
        '* item 3',
        '',
        'end of list',
        '',
    ])

    assert result == expected


@with_wikisyntax_app()
def test_ol(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'ol.wiki').text(encoding='utf-8'))

    expected = '\n'.join([
        'Ordered List:',
        '',
        '# first item',
        '',
        '# second item',
        '',
        '# third item',
        '',
        'End of list',
        '',
    ])

    assert result == expected


@with_wikisyntax_app()
def test_table(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'table.wiki').text(encoding='utf-8'))

    expected = ''.join(s.strip() for s in """
        <table border="1">
            <tr>
                <th>A</th>
                <th>B</th>
                <th>A or B</th>
            </tr>
            <tr>
                <td>False</td>
                <td>False</td>
                <td>False</td>
            </tr>
            <tr>
                <td>True</td>
                <td>False</td>
                <td>True</td>
            </tr>
            <tr>
                <td>False</td>
                <td>True</td>
                <td>True</td>
            </tr>
            <tr>
                <td>True</td>
                <td>True</td>
                <td>True</td>
            </tr>
        </table>""".split('\n')) + '\n'

    assert result == expected


@with_wikisyntax_app()
def test_transition(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'transition.wiki').text(encoding='utf-8'))

    expected = '\n'.join([
        'Some text here.',
        '',
        '----',
        '',
        'Completely new paragraph',
        '',
    ])

    assert result == expected


@with_wikisyntax_app()
def test_titles(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'titles.wiki').text(encoding='utf-8'))

    expected = '\n'.join([
        '= Big Title =',
        'Intro',
        '',
        '== Sub-Title ==',
        'Sub-Intro',
        '',
    ])

    assert result == expected


@with_wikisyntax_app()
def test_inline(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'inline.wiki').text(encoding='utf-8'))

    expected = '\n'.join([
        "''emphasis''",
        '',
        "'''strong emphasis'''",
        '',
    ])

    assert result == expected


@with_wikisyntax_app()
def test_inline(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'doctest.wiki').text(encoding='utf-8'))

    expected = '\n'.join([
        'Some doctests:',
        '',
        '<syntaxhighlight lang="python">',
        '>>> print "This is a doctest block."',
        'This is a doctest block.',
        '</syntaxhighlight>',
        '',
        'End of tests.',
        '',
    ])

    assert result == expected


@with_wikisyntax_app()
def test_inline(app, status, warnings):
    app.builder.build_update()
    result = str((app.outdir / 'doctest.wiki').text(encoding='utf-8'))

    expected = '\n'.join([
        ':<blockquote>',
        '',
        ':Some doctests in an indented block:',
        '',
        ':<syntaxhighlight lang="python">',
        '>>> print "This is a doctest block."',
        'This is a doctest block.',
        '</syntaxhighlight>',
        ':End of tests.',
        '',
        ':</blockquote>',
        '',
    ])

    assert result == expected
