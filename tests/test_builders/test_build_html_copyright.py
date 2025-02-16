from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sphinx.testing.util import SphinxTestApp

LT = time.localtime()
LT_NEW = (2009, *LT[1:], LT.tm_zone, LT.tm_gmtoff)
LOCALTIME_2009 = type(LT)(LT_NEW)


@pytest.fixture
def no_source_date_year(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Explicitly clear SOURCE_DATE_EPOCH from the environment; this
    fixture can be used to ensure that copyright substitution logic
    does not occur during selected test cases.
    """
    with monkeypatch.context() as m:
        m.delenv('SOURCE_DATE_EPOCH', raising=False)
        yield


@pytest.fixture(
    params=[
        1199145600,  # 2008-01-01 00:00:00
        1199145599,  # 2007-12-31 23:59:59
    ]
)
def source_date_year(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[int]:
    source_date_epoch = request.param
    with monkeypatch.context() as m:
        m.setattr(time, 'localtime', lambda *a: LOCALTIME_2009)
        m.setenv('SOURCE_DATE_EPOCH', str(source_date_epoch))
        yield time.gmtime(source_date_epoch).tm_year


@pytest.mark.sphinx('html', testroot='copyright-multiline')
def test_html_multi_line_copyright(
    no_source_date_year: None, app: SphinxTestApp
) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf-8')

    # check the copyright footer line by line (empty lines ignored)
    assert '  &#169; Copyright 2006.<br/>\n' in content
    assert '  &#169; Copyright 2006-2009, Alice.<br/>\n' in content
    assert '  &#169; Copyright 2010-2013, Bob.<br/>\n' in content
    assert '  &#169; Copyright 2014-2017, Charlie.<br/>\n' in content
    assert '  &#169; Copyright 2018-2021, David.<br/>\n' in content
    assert '  &#169; Copyright 2022-2025, Eve.' in content

    # check the raw copyright footer block (empty lines included)
    assert (
        '      &#169; Copyright 2006.<br/>\n'
        '    \n'
        '      &#169; Copyright 2006-2009, Alice.<br/>\n'
        '    \n'
        '      &#169; Copyright 2010-2013, Bob.<br/>\n'
        '    \n'
        '      &#169; Copyright 2014-2017, Charlie.<br/>\n'
        '    \n'
        '      &#169; Copyright 2018-2021, David.<br/>\n'
        '    \n'
        '      &#169; Copyright 2022-2025, Eve.'
    ) in content


@pytest.mark.sphinx('html', testroot='copyright-multiline')
def test_html_multi_line_copyright_sde(
    source_date_year: None, app: SphinxTestApp
) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf-8')

    # check the copyright footer line by line (empty lines ignored)
    assert '  &#169; Copyright 2006.<br/>\n' in content
    assert f'  &#169; Copyright 2006-{source_date_year}, Alice.<br/>\n' in content
    assert '  &#169; Copyright 2010-2013, Bob.<br/>\n' in content
    assert '  &#169; Copyright 2014-2017, Charlie.<br/>\n' in content
    assert '  &#169; Copyright 2018-2021, David.<br/>\n' in content
    assert '  &#169; Copyright 2022-2025, Eve.' in content

    # check the raw copyright footer block (empty lines included)
    assert (
        '      &#169; Copyright 2006.<br/>\n'
        '    \n'
        f'      &#169; Copyright 2006-{source_date_year}, Alice.<br/>\n'
        '    \n'
        '      &#169; Copyright 2010-2013, Bob.<br/>\n'
        '    \n'
        '      &#169; Copyright 2014-2017, Charlie.<br/>\n'
        '    \n'
        '      &#169; Copyright 2018-2021, David.<br/>\n'
        '    \n'
        '      &#169; Copyright 2022-2025, Eve.'
    ) in content
