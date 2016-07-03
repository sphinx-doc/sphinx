# -*- coding: utf-8 -*-
"""
    test_util_matching
    ~~~~~~~~~~~~~~~~~~

    Tests sphinx.util.matching functions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from sphinx.util.matching import compile_matchers, Matcher


def test_compile_matchers():
    # exact matching
    pat = compile_matchers(['hello.py']).pop()
    assert pat('hello.py')
    assert not pat('hello-py')
    assert not pat('subdir/hello.py')

    # wild card (*)
    pat = compile_matchers(['hello.*']).pop()
    assert pat('hello.py')
    assert pat('hello.rst')

    pat = compile_matchers(['*.py']).pop()
    assert pat('hello.py')
    assert pat('world.py')
    assert not pat('subdir/hello.py')

    # wild card (**)
    pat = compile_matchers(['hello.**']).pop()
    assert pat('hello.py')
    assert pat('hello.rst')
    assert pat('hello.py/world.py')

    pat = compile_matchers(['**.py']).pop()
    assert pat('hello.py')
    assert pat('world.py')
    assert pat('subdir/hello.py')

    pat = compile_matchers(['**/hello.py']).pop()
    assert not pat('hello.py')
    assert pat('subdir/hello.py')
    assert pat('subdir/subdir/hello.py')

    # wild card (?)
    pat = compile_matchers(['hello.?']).pop()
    assert pat('hello.c')
    assert not pat('hello.py')

    # pattern ([...])
    pat = compile_matchers(['hello[12\\].py']).pop()
    assert pat('hello1.py')
    assert pat('hello2.py')
    assert pat('hello\\.py')
    assert not pat('hello3.py')

    pat = compile_matchers(['hello[^12].py']).pop()  # "^" is not negative identifier
    assert pat('hello1.py')
    assert pat('hello2.py')
    assert pat('hello^.py')
    assert not pat('hello3.py')

    # negative pattern ([!...])
    pat = compile_matchers(['hello[!12].py']).pop()
    assert not pat('hello1.py')
    assert not pat('hello2.py')
    assert not pat('hello/.py')  # negative pattern does not match to "/"
    assert pat('hello3.py')

    # non patterns
    pat = compile_matchers(['hello[.py']).pop()
    assert pat('hello[.py')
    assert not pat('hello.py')

    pat = compile_matchers(['hello[].py']).pop()
    assert pat('hello[].py')
    assert not pat('hello.py')

    pat = compile_matchers(['hello[!].py']).pop()
    assert pat('hello[!].py')
    assert not pat('hello.py')


def test_Matcher():
    matcher = Matcher(['hello.py', '**/world.py'])
    assert matcher('hello.py')
    assert not matcher('subdir/hello.py')
    assert matcher('world.py')
    assert matcher('subdir/world.py')
