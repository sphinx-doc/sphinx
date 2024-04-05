from __future__ import annotations

import fnmatch
import random
import re

from sphinx.testing.matcher import _engine as engine


def test_line_pattern():
    assert engine.to_line_patterns('a') == ('a',)
    assert engine.to_line_patterns(['a', 'b']) == ('a', 'b')

    p = re.compile('b')
    assert engine.to_line_patterns(p) == (p,)
    assert engine.to_line_patterns(['a', p]) == ('a', p)

    # ensure build reproducibility
    assert engine.to_line_patterns({'a', p}) == ('a', p)

    p1 = re.compile('a')
    p2 = re.compile('a', re.MULTILINE)
    p3 = re.compile('ab')
    p4 = re.compile('ab', re.MULTILINE)
    ps = (p1, p2, p3, p4)

    for _ in range(100):
        random_patterns = list(ps)
        random.shuffle(random_patterns)
        patterns: set[str | re.Pattern[str]] = {*random_patterns, 'a'}
        patterns.update(random_patterns)
        assert engine.to_line_patterns(patterns) == ('a', p1, p2, p3, p4)
        assert engine.to_line_patterns(frozenset(patterns)) == ('a', p1, p2, p3, p4)


def test_block_patterns():
    assert engine.to_block_pattern('a\nb\nc') == ('a', 'b', 'c')

    p = re.compile('a')
    assert engine.to_block_pattern(p) == (p,)
    assert engine.to_block_pattern(['a', p]) == ('a', p)


def test_format_expression():
    assert engine.format_expression(str.upper, 'a') == 'A'

    p = re.compile('')
    assert engine.format_expression(str.upper, p) is p


def test_translate_expressions():
    string, pattern = 'a*', re.compile('.*')
    inputs = (string, pattern)

    expect = [engine.string_expression(string), pattern]
    assert [*engine.translate(inputs, flavor='none')] == expect
    expect = [string.upper(), pattern]
    assert [*engine.translate(inputs, flavor='none', escape=str.upper)] == expect

    expect = [string, pattern]
    assert [*engine.translate(inputs, flavor='re')] == expect
    expect = [string.upper(), pattern]
    assert [*engine.translate(inputs, flavor='re', str2regexpr=str.upper)] == expect

    expect = [fnmatch.translate(string), pattern]
    assert [*engine.translate(inputs, flavor='fnmatch')] == expect
    expect = [string.upper(), pattern]
    assert [*engine.translate(inputs, flavor='fnmatch', str2fnmatch=str.upper)] == expect


def test_compile_patterns():
    string = 'a*'
    compiled = re.compile('.*')

    expect = (re.compile(engine.string_expression(string)), compiled)
    assert engine.compile([string, compiled], flavor='none') == expect

    expect = (re.compile(fnmatch.translate(string)), compiled)
    assert engine.compile([string, compiled], flavor='fnmatch') == expect

    expect = (re.compile(string), compiled)
    assert engine.compile([string, compiled], flavor='re') == expect
