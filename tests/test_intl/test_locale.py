"""Test locale."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx import locale

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp


@pytest.fixture(autouse=True)
def _cleanup_translations() -> Iterator[None]:
    yield
    locale.translators.clear()


def test_init(rootdir: Path) -> None:
    # not initialized yet
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'Hello world'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'

    # load locale1
    locale.init([rootdir / 'test-locale' / 'locale1'], 'en', 'myext')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'

    # load a catalog to unrelated namespace
    locale.init([rootdir / 'test-locale' / 'locale2'], 'en', 'myext', 'mynamespace')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'Hello sphinx'  # nothing changed here
    assert _('Hello reST') == 'Hello reST'

    # load locale2 in addition
    locale.init([rootdir / 'test-locale' / 'locale2'], 'en', 'myext')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'HELLO SPHINX'
    assert _('Hello reST') == 'Hello reST'


def test_init_with_unknown_language(rootdir: Path) -> None:
    locale.init([rootdir / 'test-locale' / 'locale1'], 'unknown', 'myext')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'Hello world'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'


@pytest.mark.sphinx('html', testroot='root')
def test_add_message_catalog(app: SphinxTestApp, rootdir: Path) -> None:
    app.config.language = 'en'
    app.add_message_catalog('myext', rootdir / 'test-locale' / 'locale1')
    _ = locale.get_translation('myext')
    assert _('Hello world') == 'HELLO WORLD'
    assert _('Hello sphinx') == 'Hello sphinx'
    assert _('Hello reST') == 'Hello reST'


def _empty_language_translation(rootdir: Path) -> Callable[[str], str]:
    locale_dirs, catalog = [rootdir / 'test-locale' / 'locale1'], 'myext'
    locale.translators.clear()
    locale.init(locale_dirs, language=None, catalog=catalog)
    return locale.get_translation(catalog)


def test_init_environment_language(
    rootdir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with monkeypatch.context() as m:
        m.setenv('LANGUAGE', 'en_US:en')
        _ = _empty_language_translation(rootdir)
        assert _('Hello world') == 'HELLO WORLD'

    with monkeypatch.context() as m:
        m.setenv('LANGUAGE', 'et_EE:et')
        _ = _empty_language_translation(rootdir)
        assert _('Hello world') == 'Tere maailm'
