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
from sphinx.errors import ExtensionError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp

LOCALTIME_2009 = time.gmtime(1230768000)


@pytest.fixture(
    params=[
        # test with SOURCE_DATE_EPOCH unset: no modification
        (None, None),
        ('', None),
        # test with post-2009 SOURCE_DATE_EPOCH set: copyright year should not be updated
        ('1293840000', 2011),
        ('1293839999', 2010),
        # test with pre-2009 SOURCE_DATE_EPOCH set: copyright year should be updated
        ('1199145600', 2008),
        ('1199145599', 2007),
        ('0', 1970),
    ],
)
def expect_date(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[int | None]:
    sde, expect = request.param
    with monkeypatch.context() as m:
        m.setattr(time, 'localtime', lambda *a: LOCALTIME_2009)
        if sde is not None:
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


@pytest.mark.parametrize('name', ['copyright', 'project_copyright', 'epub_copyright'])
def test_copyright_placeholders_arbitrary_text(
    name: str, expect_date: int | None
) -> None:
    cfg = Config({name: '2000–%Y; Published %Y (%m), Alice'}, {})
    if name == 'epub_copyright':
        cfg.add('epub_copyright', '', 'epub', types=str)

    evaluate_copyright_placeholders(None, cfg)  # type: ignore[arg-type]

    if expect_date is not None and expect_date <= 2009:
        assert cfg[name] == f'2000–{expect_date}; Published {expect_date} (%m), Alice'
    else:
        assert cfg[name] == '2000–2009; Published 2009 (%m), Alice'
    if name != 'epub_copyright':
        assert cfg.copyright == cfg.project_copyright


@pytest.mark.parametrize('container', [list, tuple])
def test_copyright_placeholders_sequence(
    container: type[list[str] | tuple[str, ...]], expect_date: int | None
) -> None:
    cfg = Config({'copyright': container(('2000–%Y, Alice', '2000–2009, Bob'))}, {})

    evaluate_copyright_placeholders(None, cfg)  # type: ignore[arg-type]
    correct_copyright_year(None, cfg)  # type: ignore[arg-type]

    if expect_date is not None and expect_date <= 2009:
        assert cfg.copyright == container((
            f'2000–{expect_date}, Alice',
            '2000–2009, Bob',
        ))
    else:
        assert cfg.copyright == container(('2000–2009, Alice', '2000–2009, Bob'))
    assert isinstance(cfg.copyright, container)


@pytest.mark.parametrize('name', ['copyright', 'project_copyright', 'epub_copyright'])
def test_copyright_placeholders_app(
    name: str,
    expect_date: int | None,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    (tmp_path / 'conf.py').touch()
    app = make_app(
        'epub', srcdir=tmp_path, confoverrides={name: '2000–%Y; Published %Y, Alice'}
    )

    if expect_date is not None and expect_date <= 2009:
        assert app.config[name] == f'2000–{expect_date}; Published {expect_date}, Alice'
    else:
        assert app.config[name] == '2000–2009; Published 2009, Alice'


def test_source_date_epoch_invalid_at_initialization(
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / 'conf.py').touch()
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '1_000')

    with pytest.raises(
        ExtensionError,
        match="Invalid SOURCE_DATE_EPOCH value '1_000'; expected an ASCII integer",
    ):
        make_app('dummy', srcdir=tmp_path)
