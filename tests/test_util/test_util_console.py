from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import pytest

import sphinx.util.console as term
from sphinx.util.console import strip_colors, strip_control_sequences, strip_escape_sequences

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, Final, TypeVar

    _T = TypeVar('_T')

    Style = str
    """An ANSI style (color or format) known by :mod:`sphinx.util.console`."""
    AnsiCode = str
    """An ANSI escape sequence."""

ESC: Final[str] = '\x1b'
CSI: Final[str] = '\x1b['
OSC: Final[str] = '\x1b]'
BELL: Final[str] = '\x07'


def osc_title(title: str) -> str:
    """OSC string for changing the terminal title."""
    return f'{OSC}2;{title}{BELL}'


def insert_ansi(text: str, codes: Sequence[AnsiCode], *, reset: bool = False) -> str:
    """Add ANSI escape sequences codes to *text*.

    If *reset* is True, the reset code is added at the end.

    :param text: The text to decorate.
    :param codes: A list of ANSI esc. seq. to use deprived of their CSI prefix.
    :param reset: Indicate whether to add the reset esc. seq.
    :return: The decorated text.
    """
    for code in codes:
        text = f'{code}{text}'
    if reset:
        text = term.reset(text)
    return text


def apply_style(text: str, codes: Sequence[AnsiCode | Style]) -> str:
    """Apply one or more ANSI esc. seq. to *text*.

    Each item in *codes* can either be a color name (e.g., 'blue'),
    a text decoration (e.g., 'blink') or an ANSI esc. seq. deprived
    of its CSI prefix (e.g., '34m').
    """
    for code in codes:
        if code in term.codes:
            text = term.colorize(code, text)
        else:
            text = insert_ansi(text, [code])
    return text


def powerset(
    elems: Sequence[_T], *, n: int | None = None, total: bool = True
) -> list[tuple[_T, ...]]:
    r"""Generate the powerset over *seq*.

    :param elems: The elements to get the powerset over.
    :param n: Optional maximum size of a subset.
    :param total: If false, quotient the result by :math:`\mathfrak{S}_n`.

    Example:
    -------

    .. code-block:: python

       powerset([1, 2], total=True)
       [(), (1,), (2,), (1, 2), (2, 1)]

       powerset([1, 2], total=False)
       [(), (1,), (2,), (1, 2)]
    """
    if n is None:
        n = len(elems)
    gen = itertools.permutations if total else itertools.combinations
    return list(itertools.chain.from_iterable(gen(elems, i) for i in range(n + 1)))


@pytest.mark.parametrize('invariant', [ESC, CSI, OSC])
def test_strip_invariants(invariant: str) -> None:
    assert strip_colors(invariant) == invariant
    assert strip_control_sequences(invariant) == invariant
    assert strip_escape_sequences(invariant) == invariant


# some color/style codes to use (but not composed)
_STYLES: list[tuple[AnsiCode, ...]] = [
    *[(f'{CSI}{";".join(map(str, s))}m',) for s in [range(s) for s in range(4)]],
    *powerset(['blue', 'bold']),
]
# some non-color ESC codes to use (will be composed)
_CNTRLS: list[tuple[AnsiCode, ...]] = powerset([f'{CSI}A', f'{CSI}0G', f'{CSI}1;20;128H'])


# For some reason that I (picnixz) do not understand, it is not possible to
# create a mark decorator using pytest.mark.parametrize.with_args(ids=...).
#
# As such, in order not to lose autocompletion from PyCharm, we will pass
# the custom id function to each call to `pytest.mark.parametrize`.
def _clean_id(value: Any) -> str:
    if isinstance(value, str) and not value:
        return '<empty>'

    if isinstance(value, (list, tuple)):
        if not value:
            return '()'
        return '-'.join(map(_clean_id, value))

    return repr(value)


@pytest.mark.parametrize('prefix', ['', 'raw'], ids=_clean_id)  # non-formatted part
@pytest.mark.parametrize('source', ['', 'abc\ndef', BELL], ids=_clean_id)
@pytest.mark.parametrize('style', _STYLES, ids=_clean_id)
def test_strip_style(prefix: str, source: str, style: tuple[AnsiCode, ...]) -> None:
    expect = prefix + source
    pretty = prefix + apply_style(source, style)
    assert strip_colors(pretty) == expect, (pretty, expect)


@pytest.mark.parametrize('prefix', ['', 'raw'], ids=_clean_id)  # non-formatted part
@pytest.mark.parametrize('source', ['', 'abc\ndef'], ids=_clean_id)
@pytest.mark.parametrize('style', _STYLES, ids=_clean_id)
@pytest.mark.parametrize('cntrl', _CNTRLS, ids=_clean_id)
def test_strip_cntrl(
    prefix: str, source: str, style: tuple[AnsiCode, ...], cntrl: tuple[AnsiCode, ...]
) -> None:
    expect = pretty = prefix + apply_style(source, style)
    # does nothing since there are only color sequences
    assert strip_control_sequences(pretty) == expect, (pretty, expect)

    expect = prefix + source
    pretty = prefix + insert_ansi(source, cntrl)
    # all non-color codes are removed correctly
    assert strip_control_sequences(pretty) == expect, (pretty, expect)


@pytest.mark.parametrize('prefix', ['', 'raw'], ids=_clean_id)  # non-formatted part
@pytest.mark.parametrize('source', ['', 'abc\ndef'], ids=_clean_id)
@pytest.mark.parametrize('style', _STYLES, ids=_clean_id)
@pytest.mark.parametrize('cntrl', _CNTRLS, ids=_clean_id)
def test_strip_ansi(
    prefix: str, source: str, style: tuple[AnsiCode, ...], cntrl: tuple[AnsiCode, ...]
) -> None:
    expect = prefix + source

    with_style = prefix + apply_style(source, style)
    assert strip_escape_sequences(with_style) == expect, (with_style, expect)

    with_cntrl = prefix + insert_ansi(source, cntrl)
    assert strip_escape_sequences(with_cntrl) == expect, (with_cntrl, expect)

    composed = insert_ansi(with_style, cntrl)  # add some cntrl sequences
    assert strip_escape_sequences(composed) == expect, (composed, expect)

    composed = apply_style(with_cntrl, style)  # add some color sequences
    assert strip_escape_sequences(composed) == expect, (composed, expect)
