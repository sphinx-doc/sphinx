"""Test the ``sphinx.locale.safe_format`` helper."""

from __future__ import annotations

from gettext import NullTranslations

import pytest

from sphinx import locale
from sphinx.locale import safe_format


class _CorruptedTranslations(NullTranslations):
    """A catalogue whose msgstrs contain damaged ``str.format`` placeholders."""

    def gettext(self, message: str) -> str:
        return {
            'healthy message: {name}': 'saine message: {name}',
            'keyword message: {name}': 'keyword message: {nomen}',
            'positional message: {0} and {1}': 'positional message: {0}',
            'mixed message: {0} {name}': 'mixed message: {0} {nom}',
            'reordered message: {0} then {1}': 'reordered message: {1} then {0}',
        }.get(message, message)


@pytest.fixture
def corrupted_console_catalogue(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        locale.translators, ('console', 'sphinx'), _CorruptedTranslations()
    )


def test_safe_format_without_translator_is_plain_format() -> None:
    assert safe_format('a message: {name}', name='x') == 'a message: x'
    assert safe_format('{0} and {1}', 1, 2) == '1 and 2'


def test_safe_format_returns_translated_message(
    corrupted_console_catalogue: None,
) -> None:
    assert safe_format('healthy message: {name}', name='x') == 'saine message: x'


def test_safe_format_falls_back_on_renamed_keyword(
    corrupted_console_catalogue: None,
) -> None:
    assert safe_format('keyword message: {name}', name='x') == 'keyword message: x'


def test_safe_format_falls_back_on_missing_positional(
    corrupted_console_catalogue: None,
) -> None:
    assert safe_format('positional message: {0} and {1}', 1, 2) == (
        'positional message: 1 and 2'
    )


def test_safe_format_falls_back_on_mixed_corruption(
    corrupted_console_catalogue: None,
) -> None:
    assert safe_format('mixed message: {0} {name}', 1, name='x') == (
        'mixed message: 1 x'
    )


def test_safe_format_allows_reordered_placeholders(
    corrupted_console_catalogue: None,
) -> None:
    assert safe_format('reordered message: {0} then {1}', 1, 2) == (
        'reordered message: 2 then 1'
    )


def test_safe_format_supports_other_namespaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        locale.translators, ('general', 'sphinx'), _CorruptedTranslations()
    )
    assert safe_format('keyword message: {name}', namespace='general', name='x') == (
        'keyword message: x'
    )
