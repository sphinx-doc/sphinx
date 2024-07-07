"""Test copyright year adjustment"""
from datetime import datetime, timedelta

import pytest

_LOCALTIME_YEAR = datetime.now().year  # NoQA: DTZ005
_FUTURE_MOMENT = datetime.now() + timedelta(days=400)  # NoQA: DTZ005
_FUTURE_TIMESTAMP = int(_FUTURE_MOMENT.timestamp())
_FUTURE_YEAR = _FUTURE_MOMENT.year


@pytest.fixture(
    params=[
        # test with SOURCE_DATE_EPOCH unset: no modification
        (None, f'2006-{_LOCALTIME_YEAR}'),
        # test with past SOURCE_DATE_EPOCH set: copyright year should _not_ be updated
        ('1293840000', f'2006-{_LOCALTIME_YEAR}'),
        ('1293839999', f'2006-{_LOCALTIME_YEAR}'),
        # test with +1yr SOURCE_DATE_EPOCH set: copyright year should be updated
        (f'{_FUTURE_TIMESTAMP}', f'2006-{_FUTURE_YEAR}'),
    ],

)
def expect_date(request, monkeypatch):
    sde, expect = request.param
    with monkeypatch.context() as m:
        if sde:
            m.setenv('SOURCE_DATE_EPOCH', sde)
        else:
            m.delenv('SOURCE_DATE_EPOCH', raising=False)
        yield expect


@pytest.mark.sphinx('html', testroot='correct-year')
def test_correct_year(expect_date, app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert expect_date in content


@pytest.mark.sphinx('html', testroot='correct-year',
                    confoverrides={'copyright_build_year_substitution': False})
def test_build_year_substitution_disabled(expect_date, app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert f'2006-{_LOCALTIME_YEAR}' in content
