from __future__ import annotations

import re

import pytest

from sphinx.util._timestamps import _get_source_date_epoch


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (None, None),
        ('', None),
        ('0', 0),
        ('00', 0),
        ('-0', 0),
        ('-1', -1),
        ('001234', 1234),
        ('1439131307', 1439131307),
    ],
)
def test_get_source_date_epoch(
    value: str | None,
    expected: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if value is None:
        monkeypatch.delenv('SOURCE_DATE_EPOCH', raising=False)
    else:
        monkeypatch.setenv('SOURCE_DATE_EPOCH', value)

    assert _get_source_date_epoch() == expected


@pytest.mark.parametrize(
    'value',
    ['invalid', '1439131307.5', ' ', ' 123', '123\n', '+123', '1_000', '١٢٣', '-'],
)
def test_get_source_date_epoch_invalid(
    value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('SOURCE_DATE_EPOCH', value)
    message = f'Invalid SOURCE_DATE_EPOCH value {value!r}; expected an ASCII integer'

    with pytest.raises(ValueError, match=rf'^{re.escape(message)}$'):
        _get_source_date_epoch()
