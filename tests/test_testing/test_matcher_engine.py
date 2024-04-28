from __future__ import annotations

import random
import re

import pytest

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


@pytest.mark.parametrize(('string', 'expect'), [('foo.bar', r'\Afoo\.bar\Z')])
def test_string_expression(string, expect):
    assert engine.string_expression(string) == expect
    pattern = re.compile(engine.string_expression(string))
    for func in (pattern.match, pattern.search, pattern.fullmatch):
        assert func(string) is not None
        assert func(string + '.') is None
        assert func('.' + string) is None


def test_translate_expressions():
    string, compiled = 'a*', re.compile('.*')
    patterns = (string, compiled)

    assert [*engine.translate(patterns, flavor='literal')] == [r'\Aa\*\Z', compiled]
    assert [*engine.translate(patterns, flavor='fnmatch')] == [r'(?s:a.*)\Z', compiled]
    assert [*engine.translate(patterns, flavor='re')] == [string, compiled]

    expect, func = [string.upper(), compiled], str.upper
    assert [*engine.translate(patterns, flavor='literal', escape=func)] == expect
    assert [*engine.translate(patterns, flavor='fnmatch', fnmatch_translate=func)] == expect
    assert [*engine.translate(patterns, flavor='re', regular_translate=func)] == expect


def test_compile_patterns():
    string, compiled = 'a*', re.compile('.*')
    patterns = (string, compiled)

    assert engine.compile(patterns, flavor='literal') == (re.compile(r'\Aa\*\Z'), compiled)
    assert engine.compile(patterns, flavor='fnmatch') == (re.compile(r'(?s:a.*)\Z'), compiled)
    assert engine.compile(patterns, flavor='re') == (re.compile(string), compiled)

    expect = (re.compile('A*'), compiled)
    assert engine.compile(patterns, flavor='literal', escape=str.upper) == expect
    assert engine.compile(patterns, flavor='fnmatch', fnmatch_translate=str.upper) == expect
    assert engine.compile(patterns, flavor='re', regular_translate=str.upper) == expect
