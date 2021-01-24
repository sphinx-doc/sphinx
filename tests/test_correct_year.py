"""
    test_correct_year
    ~~~~~~~~~~~~~~~~~

    Test copyright year adjustment

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pytest


@pytest.fixture(
    params=[
        # test with SOURCE_DATE_EPOCH unset: no modification
        (None, '2006-2009'),
        # test with SOURCE_DATE_EPOCH set: copyright year should be updated
        ('1293840000', '2006-2011'),
        ('1293839999', '2006-2010'),
    ],

)
def expect_date(request, monkeypatch):
    sde, expect = request.param
    if sde:
        monkeypatch.setenv('SOURCE_DATE_EPOCH', sde)
    else:
        monkeypatch.delenv('SOURCE_DATE_EPOCH', raising=False)
    yield expect


@pytest.mark.sphinx('html', testroot='correct-year')
def test_correct_year(expect_date, app):
    app.build()
    content = (app.outdir / 'index.html').read_text()
    assert expect_date in content
