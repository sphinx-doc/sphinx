from __future__ import annotations

import contextlib
import os
from typing import TYPE_CHECKING, overload

import pytest
from _pytest.scope import Scope

from sphinx.testing._internal.pytest_util import TestRootFinder

if TYPE_CHECKING:
    from typing import Any, Literal


def test_testroot_finder_empty_args():
    with pytest.raises(ValueError, match="expecting a non-empty string or None for 'path'"):
        TestRootFinder('')

    with pytest.raises(ValueError, match="expecting a non-empty string or None for 'default'"):
        TestRootFinder(None, None, '')

    with pytest.raises(ValueError, match="expecting a non-empty string or None for 'default'"):
        # prefix is allowed to be ''
        TestRootFinder(None, '', '')


@pytest.mark.parametrize('prefix', [None, '', 'test-'])
@pytest.mark.parametrize('default', [None, 'default'])
@pytest.mark.parametrize('name', [None, 'foo'])
def test_testroot_finder_no_rootdir(prefix, default, name):
    finder = TestRootFinder(prefix=prefix, default=default)
    assert finder.find(name) is None


@pytest.mark.parametrize('path', ['/'])
@pytest.mark.parametrize('prefix', [None, ''])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/foo'), (None, None)])
def test_testroot_finder_no_default_no_prefix(path, prefix, name, expect):
    finder = TestRootFinder(path, prefix)
    assert finder.find(name) == expect


@pytest.mark.parametrize('path', ['/'])
@pytest.mark.parametrize('prefix', [None, ''])
@pytest.mark.parametrize('default', ['default'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/foo'), (None, '/default')])
def test_testroot_finder_with_default(path, prefix, default, name, expect):
    finder = TestRootFinder(path, prefix, default)
    assert finder.find(name) == expect


@pytest.mark.parametrize('path', ['/'])
@pytest.mark.parametrize('prefix', ['test-'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/test-foo'), (None, None)])
def test_testroot_finder_with_prefix(path, prefix, name, expect):
    finder = TestRootFinder(path, prefix)
    assert finder.find(name) == expect


@pytest.mark.parametrize('path', ['/'])
@pytest.mark.parametrize('prefix', ['test-'])
@pytest.mark.parametrize('default', ['default'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/test-foo'), (None, '/test-default')])
def test_testroot_finder(pytester, path, prefix, default, name, expect):
    finder = TestRootFinder(path, prefix, default)
    assert finder.find(name) == expect


###############################################################################
# E2E tests
###############################################################################


# fmt: off
@overload
def e2e_with_fixture_def(  # NoQA: E704
    fixt: Literal['rootdir'], attr: Literal['path'],
    value: str | os.PathLike[str] | None, expect: str | None,
    scope: Scope,
) -> str: ...
@overload  # NoQA: E302
def e2e_with_fixture_def(  # NoQA: E704
    fixt: Literal['testroot_prefix'], attr: Literal['prefix'],
    value: str | None, expect: str,
    scope: Scope,
) -> str: ...
@overload  # NoQA: E302
def e2e_with_fixture_def(  # NoQA: E704
    fixt: Literal['default_testroot'], attr: Literal['default'],
    value: str | None, expect: str | None,
    scope: Scope,
) -> str: ...
# fmt: on
def e2e_with_fixture_def(  # NoQA: E302
    fixt: str, attr: str, value: Any, expect: Any, scope: Scope
) -> str:
    """A test with an attribute defined via a fixture.

    :param fixt: The fixture name.
    :param attr: An attribute name.
    :param value: The return value of the fixture.
    :param expect: The expected attribute value.
    :param scope: The fixture scope.
    :return: The test file source.
    """
    return f"""
import pytest

@pytest.fixture(scope={scope.value!r})
def {fixt}():
    return {value!r}

def test(testroot_finder, {fixt}):
    assert {fixt} == {value!r}
    assert testroot_finder.{attr} == {expect!r}
"""


# fmt: off
@overload
def e2e_with_parametrize(  # NoQA: E704
    fixt: Literal['rootdir'], attr: Literal['path'],
    value: str | os.PathLike[str] | None, expect: str | None,
    scope: Scope,
) -> str: ...
@overload  # NoQA: E302
def e2e_with_parametrize(  # NoQA: E704
    fixt: Literal['testroot_prefix'], attr: Literal['prefix'],
    value: str | None, expect: str,
    scope: Scope,
) -> str: ...
@overload  # NoQA: E302
def e2e_with_parametrize(  # NoQA: E704
    fixt: Literal['default_testroot'], attr: Literal['default'],
    value: str | None, expect: str | None,
    scope: Scope,
) -> str: ...
# fmt: on
def e2e_with_parametrize(  # NoQA: E302
    fixt: str, attr: str, value: Any, expect: Any, scope: Scope
) -> str:
    """A test with an attribute defined via parametrization."""
    return f"""
import pytest

@pytest.mark.parametrize({fixt!r}, [{value!r}], scope={scope.value!r})
def test(testroot_finder, {fixt}):
    assert {fixt} == {value!r}
    assert testroot_finder.{attr} == {expect!r}
"""


@pytest.mark.parametrize('scope', Scope)
@pytest.mark.parametrize('value', [None, '/'])
def test_rootdir_e2e(pytester, scope, value):
    script1 = e2e_with_fixture_def('rootdir', 'path', value, value, scope)
    script2 = e2e_with_parametrize('rootdir', 'path', value, value, scope)
    pytester.makepyfile(test_fixture_def=script1, test_parametrize=script2)
    with open(os.devnull, 'w', encoding='utf-8') as NUL, contextlib.redirect_stdout(NUL):
        res = pytester.runpytest_inprocess('-p no:xdist')
    res.assert_outcomes(passed=2)


@pytest.mark.parametrize('scope', Scope)
@pytest.mark.parametrize('value', ['my-', '', None])
def test_testroot_prefix_e2e(pytester, scope, value):
    expect = value or ''  # the constructor of TestRootFinder normalizes the prefix
    script1 = e2e_with_fixture_def('testroot_prefix', 'prefix', value, expect, scope)
    script2 = e2e_with_parametrize('testroot_prefix', 'prefix', value, expect, scope)
    pytester.makepyfile(test_fixture_def=script1, test_parametrize=script2)
    with open(os.devnull, 'w', encoding='utf-8') as NUL, contextlib.redirect_stdout(NUL):
        res = pytester.runpytest_inprocess('-p no:xdist')
    res.assert_outcomes(passed=2)


@pytest.mark.parametrize('scope', Scope)
@pytest.mark.parametrize('value', [None, 'default'])
def test_default_testroot_e2e(pytester, scope, value):
    script1 = e2e_with_fixture_def('default_testroot', 'default', value, value, scope)
    script2 = e2e_with_parametrize('default_testroot', 'default', value, value, scope)
    pytester.makepyfile(test_fixture_def=script1, test_parametrize=script2)
    with open(os.devnull, 'w', encoding='utf-8') as NUL, contextlib.redirect_stdout(NUL):
        res = pytester.runpytest_inprocess('-p no:xdist')
    res.assert_outcomes(passed=2)
