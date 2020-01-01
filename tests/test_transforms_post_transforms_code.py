"""
    test_transforms_post_transforms_code
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('html', testroot='trim_doctest_flags')
def test_trim_doctest_flags_html(app, status, warning):
    app.build()

    result = (app.outdir / 'index.html').text(encoding='utf8')
    assert 'FOO' not in result
    assert 'BAR' in result
    assert 'BAZ' not in result
    assert 'QUX' not in result
    assert 'QUUX' not in result


@pytest.mark.sphinx('latex', testroot='trim_doctest_flags')
def test_trim_doctest_flags_latex(app, status, warning):
    app.build()

    result = (app.outdir / 'python.tex').text(encoding='utf8')
    assert 'FOO' not in result
    assert 'BAR' in result
    assert 'BAZ' not in result
    assert 'QUX' not in result
    assert 'QUUX' not in result
