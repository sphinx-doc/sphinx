"""Test copyright year adjustment"""
from datetime import datetime, timedelta

import pytest

_LOCALTIME_YEAR = str(datetime.now().year)  # NoQA: DTZ005
_ORIG_CONF_COPYRIGHT = f'2006-{_LOCALTIME_YEAR}'

_FUTURE_MOMENT = datetime.now() + timedelta(days=400)  # NoQA: DTZ005
_FUTURE_TIMESTAMP = int(_FUTURE_MOMENT.timestamp())
_FUTURE_YEAR = str(_FUTURE_MOMENT.year)


@pytest.fixture(
    params=[
        # test with SOURCE_DATE_EPOCH unset: no modification
        (None, _ORIG_CONF_COPYRIGHT),
        # test with past SOURCE_DATE_EPOCH set: copyright year should be updated
        ('1293840000', '2006-2011'),
        ('1293839999', '2006-2010'),
        # test with +1yr SOURCE_DATE_EPOCH set: copyright year should _not_ be updated
        (f'{_FUTURE_TIMESTAMP}', _ORIG_CONF_COPYRIGHT),
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
