from __future__ import annotations

import itertools
import string
from typing import TYPE_CHECKING

import pytest

import sphinx.util.console as term
from sphinx.util.console import strip_colors, strip_control_sequences, strip_escape_sequences

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, Final

ESC: Final[str] = '\x1b'
CSI: Final[str] = '\x1b['
OSC: Final[str] = '\x1b]'
BELL: Final[str] = '\x07'


def osc_title(title: str) -> str:
    return f'{OSC}2;{title}{BELL}'


def insert_ansi(text: str, codes: list[str]) -> str:
    for code in codes:
        text = f'{CSI}{code}{text}'
    return text


def apply_style(text: str, style: list[str]) -> str:
    for code in style:
        if code in term.codes:
            text = term.colorize(code, text)
        else:
            text = insert_ansi(text, [code])
    return text


def poweroder(seq: Sequence[Any], *, permutations: bool = True) -> list[tuple[Any, ...]]:
    generator = itertools.permutations if permutations else itertools.combinations
    return list(itertools.chain.from_iterable((generator(seq, i) for i in range(len(seq)))))


@pytest.mark.parametrize('invariant', [ESC, CSI, OSC])
def test_strip_invariants(invariant: str) -> None:
    assert strip_colors(invariant) == invariant
    assert strip_control_sequences(invariant) == invariant
    assert strip_escape_sequences(invariant) == invariant


# some color/style codes to use (but not composed)


_STYLES = ['m', '0m', '2m', '02m', '002m', '40m', '040m', '0;1m', '40;50m', '50;30;40m']
# some non-color ESC codes to use (will be composed)
_CNTRLS = ['A', '0G', '1;20;128H']


@pytest.mark.parametrize('prefix', ['', '#', 'def '])  # non-formatted part
@pytest.mark.parametrize('source', [string.printable, BELL])
@pytest.mark.parametrize('style', [_STYLES, *poweroder(['bold', 'blink', 'blue', 'red'])])
def test_strip_style(prefix: str, source: str, style: list[str]) -> None:
    expect = prefix + source
    pretty = prefix + apply_style(source, style)
    assert strip_colors(pretty) == expect, (pretty, expect)


@pytest.mark.parametrize('prefix', ['', '#', 'def '])  # non-formatted part
@pytest.mark.parametrize('source', ['', 'abc', string.printable])
@pytest.mark.parametrize('style', [_STYLES, *poweroder(['blue', 'bold'])])
@pytest.mark.parametrize('cntrl', poweroder(_CNTRLS), ids='-'.join)
def test_strip_cntrl(prefix: str, source: str, style: list[str], cntrl: list[str]) -> None:
    expect = pretty = prefix + apply_style(source, style)
    # does nothing since there are only color sequences
    assert strip_control_sequences(pretty) == expect, (pretty, expect)

    expect = prefix + source
    pretty = prefix + insert_ansi(source, cntrl)
    # all non-color codes are removed correctly
    assert strip_control_sequences(pretty) == expect, (pretty, expect)


@pytest.mark.parametrize('prefix', ['', '#', 'def '])  # non-formatted part
@pytest.mark.parametrize('source', ['', 'abc', string.printable])
@pytest.mark.parametrize('style', [_STYLES, *poweroder(['blue', 'bold'])])
@pytest.mark.parametrize('cntrl', poweroder(_CNTRLS), ids='-'.join)
def test_strip_ansi(prefix: str, source: str, style: list[str], cntrl: list[str]) -> None:
    expect = prefix + source

    with_style = prefix + apply_style(source, style)
    assert strip_escape_sequences(with_style) == expect, (with_style, expect)

    with_cntrl = prefix + insert_ansi(source, cntrl)
    assert strip_escape_sequences(with_cntrl) == expect, (with_cntrl, expect)

    composed = insert_ansi(with_style, cntrl)  # add some cntrl sequences
    assert strip_escape_sequences(composed) == expect, (composed, expect)

    composed = apply_style(with_cntrl, style)  # add some color sequences
    assert strip_escape_sequences(composed) == expect, (composed, expect)
