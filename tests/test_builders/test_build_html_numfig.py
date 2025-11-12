"""Test the HTML builder and check output against XPath."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from tests.test_builders.xpath_data import FIGURE_CAPTION
from tests.test_builders.xpath_util import check_xpath

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from xml.etree.ElementTree import ElementTree

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='numfig')
@pytest.mark.test_params(shared_result='test_build_html_numfig')
def test_numfig_disabled_warn(app: SphinxTestApp) -> None:
    app.build()
    warnings = app.warning.getvalue()
    assert 'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.' in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' not in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' not in warnings


@pytest.mark.parametrize(
    ('fname', 'path', 'check', 'be_found'),
    [
        ('index.html', FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        ('index.html', ".//table/caption/span[@class='caption-number']", None, True),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            None,
            True,
        ),
        ('index.html', './/li/p/code/span', '^fig1$', True),
        ('index.html', './/li/p/code/span', '^Figure%s$', True),
        ('index.html', './/li/p/code/span', '^table-1$', True),
        ('index.html', './/li/p/code/span', '^Table:%s$', True),
        ('index.html', './/li/p/code/span', '^CODE_1$', True),
        ('index.html', './/li/p/code/span', '^Code-%s$', True),
        ('index.html', './/li/p/a/span', '^Section 1$', True),
        ('index.html', './/li/p/a/span', '^Section 2.1$', True),
        ('index.html', './/li/p/code/span', '^Fig.{number}$', True),
        ('index.html', './/li/p/a/span', '^Sect.1 Foo$', True),
        ('foo.html', FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        ('foo.html', ".//table/caption/span[@class='caption-number']", None, True),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            None,
            True,
        ),
        ('bar.html', FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        ('bar.html', ".//table/caption/span[@class='caption-number']", None, True),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            None,
            True,
        ),
        ('baz.html', FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        ('baz.html', ".//table/caption/span[@class='caption-number']", None, True),
        (
            'baz.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            None,
            True,
        ),
    ],
)
@pytest.mark.sphinx('html', testroot='numfig')
@pytest.mark.test_params(shared_result='test_build_html_numfig')
def test_numfig_disabled(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str | None,
    be_found: bool,
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check, be_found)


@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    srcdir='test_numfig_without_numbered_toctree_warn',
    confoverrides={'numfig': True},
)
def test_numfig_without_numbered_toctree_warn(app: SphinxTestApp) -> None:
    app.build()
    # remove :numbered: option
    index = (app.srcdir / 'index.rst').read_text(encoding='utf8')
    index = re.sub(':numbered:.*', '', index)
    (app.srcdir / 'index.rst').write_text(index, encoding='utf8')
    app.build()

    warnings = app.warning.getvalue()
    assert (
        'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.'
    ) not in warnings
    assert (
        'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index'
    ) in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize(
    ('fname', 'path', 'check', 'be_found'),
    [
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 9 $',
            True,
        ),
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 10 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 9 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 10 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 9 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 10 $',
            True,
        ),
        ('index.html', './/li/p/a/span', '^Fig. 9$', True),
        ('index.html', './/li/p/a/span', '^Figure6$', True),
        ('index.html', './/li/p/a/span', '^Table 9$', True),
        ('index.html', './/li/p/a/span', '^Table:6$', True),
        ('index.html', './/li/p/a/span', '^Listing 9$', True),
        ('index.html', './/li/p/a/span', '^Code-6$', True),
        ('index.html', './/li/p/code/span', '^foo$', True),
        ('index.html', './/li/p/code/span', '^bar_a$', True),
        ('index.html', './/li/p/a/span', '^Fig.9 should be Fig.1$', True),
        ('index.html', './/li/p/code/span', '^Sect.{number}$', True),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 3 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 4 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 3 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 4 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 3 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 4 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 5 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 7 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 8 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 5 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 7 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 8 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 5 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 7 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 8 $',
            True,
        ),
        (
            'baz.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 6 $',
            True,
        ),
        (
            'baz.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 6 $',
            True,
        ),
        (
            'baz.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 6 $',
            True,
        ),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    srcdir='test_numfig_without_numbered_toctree',
    confoverrides={'numfig': True},
)
def test_numfig_without_numbered_toctree(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str | None,
    be_found: bool,
) -> None:
    # remove :numbered: option
    index = (app.srcdir / 'index.rst').read_text(encoding='utf8')
    index = re.sub(':numbered:.*', '', index)
    (app.srcdir / 'index.rst').write_text(index, encoding='utf8')

    if not list(app.outdir.iterdir()):
        app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check, be_found)


@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    confoverrides={'numfig': True},
)
@pytest.mark.test_params(shared_result='test_build_html_numfig_on')
def test_numfig_with_numbered_toctree_warn(app: SphinxTestApp) -> None:
    app.build()
    warnings = app.warning.getvalue()
    assert (
        'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.'
    ) not in warnings
    assert (
        'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index'
    ) in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize(
    ('fname', 'path', 'check', 'be_found'),
    [
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1 $',
            True,
        ),
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2 $',
            True,
        ),
        ('index.html', './/li/p/a/span', '^Fig. 1$', True),
        ('index.html', './/li/p/a/span', '^Figure2.2$', True),
        ('index.html', './/li/p/a/span', '^Table 1$', True),
        ('index.html', './/li/p/a/span', '^Table:2.2$', True),
        ('index.html', './/li/p/a/span', '^Listing 1$', True),
        ('index.html', './/li/p/a/span', '^Code-2.2$', True),
        ('index.html', './/li/p/a/span', '^Section.1$', True),
        ('index.html', './/li/p/a/span', '^Section.2.1$', True),
        ('index.html', './/li/p/a/span', '^Fig.1 should be Fig.1$', True),
        ('index.html', './/li/p/a/span', '^Sect.1 Foo$', True),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.1 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.2 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.3 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.4 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.2 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.3 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.4 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.2 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.3 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.4 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.1 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.3 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.4 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.1 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.3 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.4 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.1 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.3 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.4 $',
            True,
        ),
        (
            'baz.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.2 $',
            True,
        ),
        (
            'baz.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.2 $',
            True,
        ),
        (
            'baz.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.2 $',
            True,
        ),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    confoverrides={'numfig': True},
)
@pytest.mark.test_params(shared_result='test_build_html_numfig_on')
def test_numfig_with_numbered_toctree(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str | None,
    be_found: bool,
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check, be_found)


@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    confoverrides={
        'numfig': True,
        'numfig_format': {
            'figure': 'Figure:%s',
            'table': 'Tab_%s',
            'code-block': 'Code-%s',
            'section': 'SECTION-%s',
        },
    },
)
@pytest.mark.test_params(shared_result='test_build_html_numfig_format_warn')
def test_numfig_with_prefix_warn(app: SphinxTestApp) -> None:
    app.build()
    warnings = app.warning.getvalue()
    assert (
        'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.'
    ) not in warnings
    assert (
        'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index'
    ) in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize(
    ('fname', 'path', 'check', 'be_found'),
    [
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:1 $',
            True,
        ),
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:2 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_1 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_2 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-1 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-2 $',
            True,
        ),
        ('index.html', './/li/p/a/span', '^Figure:1$', True),
        ('index.html', './/li/p/a/span', '^Figure2.2$', True),
        ('index.html', './/li/p/a/span', '^Tab_1$', True),
        ('index.html', './/li/p/a/span', '^Table:2.2$', True),
        ('index.html', './/li/p/a/span', '^Code-1$', True),
        ('index.html', './/li/p/a/span', '^Code-2.2$', True),
        ('index.html', './/li/p/a/span', '^SECTION-1$', True),
        ('index.html', './/li/p/a/span', '^SECTION-2.1$', True),
        ('index.html', './/li/p/a/span', '^Fig.1 should be Fig.1$', True),
        ('index.html', './/li/p/a/span', '^Sect.1 Foo$', True),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:1.1 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:1.2 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:1.3 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:1.4 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_1.2 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_1.3 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_1.4 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-1.2 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-1.3 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-1.4 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:2.1 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:2.3 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:2.4 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_2.1 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_2.3 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_2.4 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-2.1 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-2.3 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-2.4 $',
            True,
        ),
        (
            'baz.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Figure:2.2 $',
            True,
        ),
        (
            'baz.html',
            ".//table/caption/span[@class='caption-number']",
            '^Tab_2.2 $',
            True,
        ),
        (
            'baz.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Code-2.2 $',
            True,
        ),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    confoverrides={
        'numfig': True,
        'numfig_format': {
            'figure': 'Figure:%s',
            'table': 'Tab_%s',
            'code-block': 'Code-%s',
            'section': 'SECTION-%s',
        },
    },
)
@pytest.mark.test_params(shared_result='test_build_html_numfig_format_warn')
def test_numfig_with_prefix(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str | None,
    be_found: bool,
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check, be_found)


@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    confoverrides={'numfig': True, 'numfig_secnum_depth': 2},
)
@pytest.mark.test_params(shared_result='test_build_html_numfig_depth_2')
def test_numfig_with_secnum_depth_warn(app: SphinxTestApp) -> None:
    app.build()
    warnings = app.warning.getvalue()
    assert (
        'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.'
    ) not in warnings
    assert (
        'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index'
    ) in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize(
    ('fname', 'path', 'check', 'be_found'),
    [
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1 $',
            True,
        ),
        (
            'index.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1 $',
            True,
        ),
        (
            'index.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1 $',
            True,
        ),
        (
            'index.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2 $',
            True,
        ),
        ('index.html', './/li/p/a/span', '^Fig. 1$', True),
        ('index.html', './/li/p/a/span', '^Figure2.1.2$', True),
        ('index.html', './/li/p/a/span', '^Table 1$', True),
        ('index.html', './/li/p/a/span', '^Table:2.1.2$', True),
        ('index.html', './/li/p/a/span', '^Listing 1$', True),
        ('index.html', './/li/p/a/span', '^Code-2.1.2$', True),
        ('index.html', './/li/p/a/span', '^Section.1$', True),
        ('index.html', './/li/p/a/span', '^Section.2.1$', True),
        ('index.html', './/li/p/a/span', '^Fig.1 should be Fig.1$', True),
        ('index.html', './/li/p/a/span', '^Sect.1 Foo$', True),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.1 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.1.1 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.1.2 $',
            True,
        ),
        (
            'foo.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 1.2.1 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.1.2 $',
            True,
        ),
        (
            'foo.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 1.2.1 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.1.1 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.1.2 $',
            True,
        ),
        (
            'foo.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.2.1 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.1.1 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.1.3 $',
            True,
        ),
        (
            'bar.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.2.1 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.1.1 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.1.3 $',
            True,
        ),
        (
            'bar.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.2.1 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.1.1 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.1.3 $',
            True,
        ),
        (
            'bar.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.2.1 $',
            True,
        ),
        (
            'baz.html',
            FIGURE_CAPTION + "/span[@class='caption-number']",
            '^Fig. 2.1.2 $',
            True,
        ),
        (
            'baz.html',
            ".//table/caption/span[@class='caption-number']",
            '^Table 2.1.2 $',
            True,
        ),
        (
            'baz.html',
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.1.2 $',
            True,
        ),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='numfig',
    confoverrides={'numfig': True, 'numfig_secnum_depth': 2},
)
@pytest.mark.test_params(shared_result='test_build_html_numfig_depth_2')
def test_numfig_with_secnum_depth(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str | None,
    be_found: bool,
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check, be_found)


@pytest.mark.parametrize(
    'expect',
    [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 1 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 2 $', True),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1 $',
            True,
        ),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2 $',
            True,
        ),
        ('.//li/p/a/span', '^Fig. 1$', True),
        ('.//li/p/a/span', '^Figure2.2$', True),
        ('.//li/p/a/span', '^Table 1$', True),
        ('.//li/p/a/span', '^Table:2.2$', True),
        ('.//li/p/a/span', '^Listing 1$', True),
        ('.//li/p/a/span', '^Code-2.2$', True),
        ('.//li/p/a/span', '^Section.1$', True),
        ('.//li/p/a/span', '^Section.2.1$', True),
        ('.//li/p/a/span', '^Fig.1 should be Fig.1$', True),
        ('.//li/p/a/span', '^Sect.1 Foo$', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.2 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.4 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 1.1 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 1.2 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 1.3 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 1.4 $', True),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.1 $',
            True,
        ),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.2 $',
            True,
        ),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.3 $',
            True,
        ),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 1.4 $',
            True,
        ),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.4 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 2.1 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 2.3 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 2.4 $', True),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.1 $',
            True,
        ),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.3 $',
            True,
        ),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.4 $',
            True,
        ),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.2 $', True),
        (".//table/caption/span[@class='caption-number']", '^Table 2.2 $', True),
        (
            ".//div[@class='code-block-caption']/span[@class='caption-number']",
            '^Listing 2.2 $',
            True,
        ),
    ],
)
@pytest.mark.sphinx(
    'singlehtml',
    testroot='numfig',
    confoverrides={'numfig': True},
)
@pytest.mark.test_params(shared_result='test_build_html_numfig_on')
def test_numfig_with_singlehtml(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    expect: tuple[str, str, bool],
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / 'index.html'), 'index.html', *expect)
