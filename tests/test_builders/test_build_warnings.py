from __future__ import annotations

import os
import re
import sys
import traceback
from typing import TYPE_CHECKING

import pytest

from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.errors import SphinxError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp

ENV_WARNINGS = """\
{root}/autodoc_fodder.py:docstring of autodoc_fodder.MarkupError:\\d+: \
WARNING: Explicit markup ends without a blank line; unexpected unindent. \\[docutils\\]
{root}/index.rst:\\d+: WARNING: Encoding 'utf-8-sig' used for reading included \
file '{root}/wrongenc.inc' seems to be wrong, try giving an :encoding: option \\[docutils\\]
{root}/index.rst:\\d+: WARNING: invalid single index entry '' \\[index\\]
{root}/index.rst:\\d+: WARNING: image file not readable: foo.png \\[image.not_readable\\]
{root}/index.rst:\\d+: WARNING: download file not readable: {root}/nonexisting.png \\[download.not_readable\\]
"""

HTML_WARNINGS = (
    ENV_WARNINGS
    + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option' \\[ref.option\\]
{root}/index.rst:\\d+: WARNING: citation not found: missing \\[ref.ref\\]
{root}/index.rst:\\d+: WARNING: a suitable image for html builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: Lexing literal_block ".*" as "c" resulted in an error at token: ".*". Retrying in relaxed mode. \\[misc.highlighting_failure\\]
"""
)

LATEX_WARNINGS = (
    ENV_WARNINGS
    + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option' \\[ref.option\\]
{root}/index.rst:\\d+: WARNING: citation not found: missing \\[ref.ref\\]
{root}/index.rst:\\d+: WARNING: a suitable image for latex builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: Lexing literal_block ".*" as "c" resulted in an error at token: ".*". Retrying in relaxed mode. \\[misc.highlighting_failure\\]
"""
)

TEXINFO_WARNINGS = (
    ENV_WARNINGS
    + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option' \\[ref.option\\]
{root}/index.rst:\\d+: WARNING: citation not found: missing \\[ref.ref\\]
{root}/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: \
\\['application/pdf', 'image/svg\\+xml'\\] \\(svgimg.\\*\\)
"""
)


def _check_warnings(expected_warnings: str, warning: str) -> None:
    warnings = strip_escape_sequences(re.sub(re.escape(os.sep) + '{1,2}', '/', warning))
    assert re.match(f'{expected_warnings}$', warnings), (
        "Warnings don't match:\n"
        f'--- Expected (regex):\n{expected_warnings}\n'
        f'--- Got:\n{warnings}'
    )
    sys.modules.pop('autodoc_fodder', None)


@pytest.mark.sphinx(
    'html',
    testroot='warnings',
    freshenv=True,
)
def test_html_warnings(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    warnings_exp = HTML_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    _check_warnings(warnings_exp, app.warning.getvalue())


@pytest.mark.sphinx(
    'html',
    testroot='warnings',
    freshenv=True,
    exception_on_warning=True,
)
def test_html_warnings_exception_on_warning(app: SphinxTestApp) -> None:
    try:
        app.build(force_all=True)
        pytest.fail('Expected an exception to be raised')
    except SphinxError:
        tb = traceback.format_exc()
        assert 'unindent_warning' in tb
        assert 'pending_warnings' not in tb


@pytest.mark.sphinx(
    'latex',
    testroot='warnings',
    freshenv=True,
)
def test_latex_warnings(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    warnings_exp = LATEX_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    _check_warnings(warnings_exp, app.warning.getvalue())


@pytest.mark.sphinx(
    'texinfo',
    testroot='warnings',
    freshenv=True,
)
def test_texinfo_warnings(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    warnings_exp = TEXINFO_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    _check_warnings(warnings_exp, app.warning.getvalue())


def test_uncacheable_config_warning(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """Test that an unpickleable config value raises a warning."""
    tmp_path.joinpath('conf.py').write_text(
        """\
my_config = lambda: None
show_warning_types = True
def setup(app):
    app.add_config_value('my_config', None, 'env')
    """,
        encoding='utf-8',
    )
    tmp_path.joinpath('index.rst').write_text('Test\n====\n', encoding='utf-8')
    app = make_app(srcdir=tmp_path)
    app.build()
    assert strip_escape_sequences(app.warning.getvalue()).strip() == (
        "WARNING: cannot cache unpickleable configuration value: 'my_config' "
        '(because it contains a function, class, or module object) [config.cache]'
    )
