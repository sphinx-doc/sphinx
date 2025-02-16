"""Test all builders.

This test skips building docs for some builders that have independent testcases.
(html, changes, epub, latex, texinfo and manpage)
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from unittest.mock import MagicMock

    from sphinx.testing.util import SphinxTestApp


def request_session_head(url: str, **kwargs: object) -> mock.Mock:
    response = mock.Mock()
    response.status_code = 200
    response.url = url
    return response


@pytest.fixture
def nonascii_srcdir(rootdir: Path, sphinx_test_tempdir: Path) -> Path:
    # Build in a non-ASCII source dir
    test_name = '\u65e5\u672c\u8a9e'
    srcdir = sphinx_test_tempdir / 'test_build_all' / test_name
    if not srcdir.exists():
        shutil.copytree(rootdir / 'test-root', srcdir)

    # add a doc with a non-ASCII file name to the source dir
    (srcdir / f'{test_name}.txt').write_text(
        'non-ascii file name page\n========================\n', encoding='utf8'
    )

    with srcdir.joinpath('index.txt').open('a', encoding='utf8') as f:
        f.write(f"""
.. toctree::

   {test_name}/{test_name}
""")
    return srcdir


def test_build_dirhtml(
    make_app: Callable[..., SphinxTestApp], nonascii_srcdir: Path
) -> None:
    app = make_app('dirhtml', srcdir=nonascii_srcdir)
    app.build(force_all=True)


def test_build_singlehtml(
    make_app: Callable[..., SphinxTestApp], nonascii_srcdir: Path
) -> None:
    app = make_app('singlehtml', srcdir=nonascii_srcdir)
    app.build(force_all=True)


def test_build_text(
    make_app: Callable[..., SphinxTestApp], nonascii_srcdir: Path
) -> None:
    app = make_app('text', srcdir=nonascii_srcdir)
    app.build(force_all=True)


def test_build_xml(
    make_app: Callable[..., SphinxTestApp], nonascii_srcdir: Path
) -> None:
    app = make_app('xml', srcdir=nonascii_srcdir)
    app.build(force_all=True)


def test_build_pseudoxml(
    make_app: Callable[..., SphinxTestApp], nonascii_srcdir: Path
) -> None:
    app = make_app('pseudoxml', srcdir=nonascii_srcdir)
    app.build(force_all=True)


@mock.patch(
    'sphinx.builders.linkcheck.requests.head',
    side_effect=request_session_head,
)
def test_build_linkcheck(
    requests_head: MagicMock,
    make_app: Callable[..., SphinxTestApp],
    nonascii_srcdir: Path,
) -> None:
    app = make_app('linkcheck', srcdir=nonascii_srcdir)
    app.build(force_all=True)
