"""Test the HTML builder and check output against XPath."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.test_builders.xpath_html_util import _intradocument_hyperlink_check
from tests.test_builders.xpath_util import check_xpath

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from xml.etree.ElementTree import ElementTree

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.parametrize(
    ('fname', 'path', 'check', 'be_found'),
    [
        # index.html
        ('index.html', ".//li[@class='toctree-l3']/a", '1.1.1. Foo A1', True),
        ('index.html', ".//li[@class='toctree-l3']/a", '1.2.1. Foo B1', True),
        ('index.html', ".//li[@class='toctree-l3']/a", '2.1.1. Bar A1', False),
        ('index.html', ".//li[@class='toctree-l3']/a", '2.2.1. Bar B1', False),
        # foo.html
        ('foo.html', './/h1', 'Foo', True),
        ('foo.html', './/h2', 'Foo A', True),
        ('foo.html', './/h3', 'Foo A1', True),
        ('foo.html', './/h2', 'Foo B', True),
        ('foo.html', './/h3', 'Foo B1', True),
        # foo.html section-number
        ('foo.html', ".//h1//span[@class='section-number']", '1. ', True),
        ('foo.html', ".//h2//span[@class='section-number']", '1.1. ', True),
        ('foo.html', ".//h3//span[@class='section-number']", '1.1.1. ', True),
        ('foo.html', ".//h2//span[@class='section-number']", '1.2. ', True),
        ('foo.html', ".//h3//span[@class='section-number']", '1.2.1. ', True),
        # foo.html sphinxsidebarwrapper
        ('foo.html', ".//div[@class='sphinxsidebarwrapper']//li/a", '1.1. Foo A', True),
        (
            'foo.html',
            ".//div[@class='sphinxsidebarwrapper']//li/a",
            '1.1.1. Foo A1',
            True,
        ),
        ('foo.html', ".//div[@class='sphinxsidebarwrapper']//li/a", '1.2. Foo B', True),
        (
            'foo.html',
            ".//div[@class='sphinxsidebarwrapper']//li/a",
            '1.2.1. Foo B1',
            True,
        ),
        # bar.html
        ('bar.html', './/h1', 'Bar', True),
        ('bar.html', './/h2', 'Bar A', True),
        ('bar.html', './/h2', 'Bar B', True),
        ('bar.html', './/h3', 'Bar B1', True),
        ('bar.html', ".//h1//span[@class='section-number']", '2. ', True),
        ('bar.html', ".//h2//span[@class='section-number']", '2.1. ', True),
        ('bar.html', ".//h2//span[@class='section-number']", '2.2. ', True),
        ('bar.html', ".//h3//span[@class='section-number']", '2.2.1. ', True),
        ('bar.html', ".//div[@class='sphinxsidebarwrapper']//li/a", '2. Bar', True),
        ('bar.html', ".//div[@class='sphinxsidebarwrapper']//li/a", '2.1. Bar A', True),
        ('bar.html', ".//div[@class='sphinxsidebarwrapper']//li/a", '2.2. Bar B', True),
        (
            'bar.html',
            ".//div[@class='sphinxsidebarwrapper']//li/a",
            '2.2.1. Bar B1',
            False,
        ),
        # baz.html
        ('baz.html', './/h1', 'Baz A', True),
        ('baz.html', ".//h1//span[@class='section-number']", '2.1.1. ', True),
    ],
)
@pytest.mark.sphinx('html', testroot='tocdepth')
@pytest.mark.test_params(shared_result='test_build_html_tocdepth')
def test_tocdepth(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str,
    be_found: bool,
) -> None:
    app.build()
    # https://github.com/sphinx-doc/sphinx/issues/1251
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check, be_found)


@pytest.mark.parametrize(
    'expect',
    [
        (".//li[@class='toctree-l3']/a", '1.1.1. Foo A1', True),
        (".//li[@class='toctree-l3']/a", '1.2.1. Foo B1', True),
        (".//li[@class='toctree-l3']/a", '2.1.1. Bar A1', False),
        (".//li[@class='toctree-l3']/a", '2.2.1. Bar B1', False),
        (".//ul/li[@class='toctree-l1']/..//a", _intradocument_hyperlink_check),
        # index.rst
        ('.//h1', 'test-tocdepth', True),
        # foo.rst
        ('.//h2', 'Foo', True),
        ('.//h3', 'Foo A', True),
        ('.//h4', 'Foo A1', True),
        ('.//h3', 'Foo B', True),
        ('.//h4', 'Foo B1', True),
        (".//h2//span[@class='section-number']", '1. ', True),
        (".//h3//span[@class='section-number']", '1.1. ', True),
        (".//h4//span[@class='section-number']", '1.1.1. ', True),
        (".//h3//span[@class='section-number']", '1.2. ', True),
        (".//h4//span[@class='section-number']", '1.2.1. ', True),
        # bar.rst
        ('.//h2', 'Bar', True),
        ('.//h3', 'Bar A', True),
        ('.//h3', 'Bar B', True),
        ('.//h4', 'Bar B1', True),
        (".//h2//span[@class='section-number']", '2. ', True),
        (".//h3//span[@class='section-number']", '2.1. ', True),
        (".//h3//span[@class='section-number']", '2.2. ', True),
        (".//h4//span[@class='section-number']", '2.2.1. ', True),
        # baz.rst
        ('.//h4', 'Baz A', True),
        (".//h4//span[@class='section-number']", '2.1.1. ', True),
    ],
)
@pytest.mark.sphinx('singlehtml', testroot='tocdepth')
@pytest.mark.test_params(shared_result='test_build_html_tocdepth')
def test_tocdepth_singlehtml(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    expect: tuple[str, str, bool],
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / 'index.html'), 'index.html', *expect)
