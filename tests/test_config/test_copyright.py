"""Test copyright year adjustment"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from sphinx.config import (
    Config,
    correct_copyright_year,
    evaluate_copyright_placeholders,
)
from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp

LT = time.localtime()
LT_NEW = (2009, *LT[1:], LT.tm_zone, LT.tm_gmtoff)
LOCALTIME_2009 = type(LT)(LT_NEW)

GT = time.gmtime()
GT_NEW = (2009, *GT[1:], GT.tm_zone, GT.tm_gmtoff)
GMTTIME_2009 = type(GT)(GT_NEW)


@pytest.fixture(
    params=[
        # test with SOURCE_DATE_EPOCH unset: no modification
        (None, None),
        # test with post-2009 SOURCE_DATE_EPOCH set: copyright year should not be updated
        ('1293840000', 2011),
        ('1293839999', 2010),
        # test with pre-2009 SOURCE_DATE_EPOCH set: copyright year should be updated
        ('1199145600', 2008),
        ('1199145599', 2007),
    ],
)
def expect_date(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[int | None]:
    sde, expect = request.param
    with monkeypatch.context() as m:
        lt_orig, gmtt_orig = time.localtime, time.gmtime
        m.setattr(time, 'localtime', lambda *a: lt_orig(*a) if a else LOCALTIME_2009)
        m.setattr(time, 'gmtime', lambda *a: gmtt_orig(*a) if a else GMTTIME_2009)
        if sde:
            m.setenv('SOURCE_DATE_EPOCH', sde)
        else:
            m.delenv('SOURCE_DATE_EPOCH', raising=False)
        yield expect


def test_correct_year(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_date = '2006-2009, Alice'
    cfg = Config({'copyright': copyright_date}, {})
    assert cfg.copyright == copyright_date
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == f'2006-{expect_date}, Alice'
    else:
        assert cfg.copyright == copyright_date


def test_correct_year_space(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_date = '2006-2009 Alice'
    cfg = Config({'copyright': copyright_date}, {})
    assert cfg.copyright == copyright_date
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == f'2006-{expect_date} Alice'
    else:
        assert cfg.copyright == copyright_date


def test_correct_year_no_author(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_date = '2006-2009'
    cfg = Config({'copyright': copyright_date}, {})
    assert cfg.copyright == copyright_date
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == f'2006-{expect_date}'
    else:
        assert cfg.copyright == copyright_date


def test_correct_year_single(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_date = '2009, Alice'
    cfg = Config({'copyright': copyright_date}, {})
    assert cfg.copyright == copyright_date
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == f'{expect_date}, Alice'
    else:
        assert cfg.copyright == copyright_date


def test_correct_year_single_space(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_date = '2009 Alice'
    cfg = Config({'copyright': copyright_date}, {})
    assert cfg.copyright == copyright_date
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == f'{expect_date} Alice'
    else:
        assert cfg.copyright == copyright_date


def test_correct_year_single_no_author(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_date = '2009'
    cfg = Config({'copyright': copyright_date}, {})
    assert cfg.copyright == copyright_date
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == f'{expect_date}'
    else:
        assert cfg.copyright == copyright_date


def test_correct_year_placeholder(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_date = '2006-%Y, Alice'
    cfg = Config({'copyright': copyright_date}, {})
    assert cfg.copyright == copyright_date
    evaluate_copyright_placeholders(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == f'2006-{expect_date}, Alice'
    else:
        assert cfg.copyright == '2006-2009, Alice'


def test_correct_year_multi_line(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_dates = (
        '2009',
        '2006-2009, Alice',
        '2010-2013, Bob',
        '2014-2017, Charlie',
        '2018-2021, David',
        '2022-2025, Eve',
    )
    cfg = Config({'copyright': copyright_dates}, {})
    assert cfg.copyright == copyright_dates
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == (
            f'{expect_date}',
            f'2006-{expect_date}, Alice',
            # post 2009-dates aren't substituted
            '2010-2013, Bob',
            '2014-2017, Charlie',
            '2018-2021, David',
            '2022-2025, Eve',
        )
    else:
        assert cfg.copyright == copyright_dates


def test_correct_year_multi_line_all_formats(expect_date: int | None) -> None:
    # test that copyright is substituted
    copyright_dates = (
        '2009',
        '2009 Alice',
        '2009, Bob',
        '2006-2009',
        '2006-2009 Charlie',
        '2006-2009, David',
    )
    cfg = Config({'copyright': copyright_dates}, {})
    assert cfg.copyright == copyright_dates
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == (
            f'{expect_date}',
            f'{expect_date} Alice',
            f'{expect_date}, Bob',
            f'2006-{expect_date}',
            f'2006-{expect_date} Charlie',
            f'2006-{expect_date}, David',
        )
    else:
        assert cfg.copyright == copyright_dates


def test_correct_year_multi_line_all_formats_placeholder(
    expect_date: int | None,
) -> None:
    # test that copyright is substituted
    copyright_dates = (
        '%Y',
        '%Y Alice',
        '%Y, Bob',
        '2006-%Y',
        '2006-%Y Charlie',
        '2006-%Y, David',
        # other format codes are left as-is
        '2006-%y, Eve',
        '%Y-%m-%d %H:%M:S %z, Francis',
        # non-ascii range patterns are supported
        '2000–%Y Guinevere',
    )
    cfg = Config({'copyright': copyright_dates}, {})
    assert cfg.copyright == copyright_dates
    evaluate_copyright_placeholders(None, cfg)  # type: ignore[arg-type]
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert cfg.copyright == (
            f'{expect_date}',
            f'{expect_date} Alice',
            f'{expect_date}, Bob',
            f'2006-{expect_date}',
            f'2006-{expect_date} Charlie',
            f'2006-{expect_date}, David',
            '2006-%y, Eve',
            f'{expect_date}-%m-%d %H:%M:S %z, Francis',
            f'2000–{expect_date} Guinevere',
        )
    else:
        assert cfg.copyright == (
            '2009',
            '2009 Alice',
            '2009, Bob',
            '2006-2009',
            '2006-2009 Charlie',
            '2006-2009, David',
            '2006-%y, Eve',
            '2009-%m-%d %H:%M:S %z, Francis',
            '2000–2009 Guinevere',
        )


def test_correct_year_app(
    expect_date: int | None,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    # integration test
    copyright_date = '2006-2009, Alice'
    (tmp_path / 'conf.py').touch()
    app = make_app(
        'dummy',
        srcdir=tmp_path,
        confoverrides={'copyright': copyright_date},
    )
    if expect_date and expect_date <= LOCALTIME_2009.tm_year:
        assert app.config.copyright == f'2006-{expect_date}, Alice'
    else:
        assert app.config.copyright == copyright_date
