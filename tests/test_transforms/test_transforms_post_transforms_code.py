import pytest


@pytest.mark.sphinx('html', testroot='trim_doctest_flags')
def test_trim_doctest_flags_html(app):
    app.build()

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'FOO' not in result
    assert 'BAR' in result
    assert 'BAZ' not in result
    assert 'QUX' not in result
    assert 'QUUX' not in result
    assert 'CORGE' not in result
    assert 'GRAULT' in result


@pytest.mark.sphinx(
    'html',
    testroot='trim_doctest_flags',
    confoverrides={'trim_doctest_flags': False},
)
def test_trim_doctest_flags_disabled(app):
    app.build()

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'FOO' in result
    assert 'BAR' in result
    assert 'BAZ' in result
    assert 'QUX' in result
    assert 'QUUX' not in result
    assert 'CORGE' not in result
    assert 'GRAULT' in result


@pytest.mark.sphinx('latex', testroot='trim_doctest_flags')
def test_trim_doctest_flags_latex(app):
    app.build()

    result = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    assert 'FOO' not in result
    assert 'BAR' in result
    assert 'BAZ' not in result
    assert 'QUX' not in result
    assert 'QUUX' not in result
    assert 'CORGE' not in result
    assert 'GRAULT' in result
