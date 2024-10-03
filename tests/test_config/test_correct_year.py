"""Test copyright year adjustment"""

import time

import pytest

_LT = time.localtime()
_LOCALTIME_2009 = type(_LT)((2009, *_LT[1:], _LT.tm_zone, _LT.tm_gmtoff))


@pytest.fixture(
    params=[
        # test with SOURCE_DATE_EPOCH unset: no modification
        (None, '2006-2009'),
        # test with past SOURCE_DATE_EPOCH set: copyright year should be updated
        ('1199145600', '2006-2008'),
        ('1199145599', '2006-2007'),
        # test with future SOURCE_DATE_EPOCH set: copyright year should not be updated
        ('1293840000', '2006-2009'),
        ('1293839999', '2006-2009'),

    ],
)
def expect_date(request, monkeypatch):

    sde, expect = request.param
    with monkeypatch.context() as m:
        m.setattr(time, 'localtime', lambda *a: _LOCALTIME_2009)
        if sde:
            m.setenv('SOURCE_DATE_EPOCH', sde)
        else:
            m.delenv('SOURCE_DATE_EPOCH', raising=False)
        yield expect


@pytest.mark.sphinx('html', testroot='correct-year')
def test_correct_year(expect_date, app):
    assert expect_date in app.config.copyright
