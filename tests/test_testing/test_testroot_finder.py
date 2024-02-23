from __future__ import annotations

from typing import Any

import pytest
from _pytest.scope import Scope

from sphinx.testing.pytest_util import TestRootFinder


def chk_testroot_finder_with_fixtures(
    pytester: pytest.Pytester,
    fixturename: str,
    attrname: str,
    value: Any,
    expect: Any,
) -> None:
    def fixtured(scope: str) -> str:
        return f'''
import pytest

@pytest.fixture(scope={scope!r})
def {fixturename}():
    return {value!r}

def test(testroot_finder, {fixturename}):
    assert testroot_finder.{attrname} == {expect!r}
'''

    def indirect(scope: str) -> str:
        return f'''
import pytest

@pytest.mark.parametrize({fixturename!r}, [{value!r}], scope={scope!r}, indirect=True)
def test(testroot_finder, {fixturename}):
    assert {fixturename} == {value!r}
    assert testroot_finder.{attrname} == {expect!r}
'''

    scopes = [scope.value for scope in Scope]
    fixtured_tests = {f'test_testroot_finder_fixtured_{scope}': fixtured(scope) for scope in scopes}
    pytester.makepyfile(**fixtured_tests)
    indirect_tests = {f'test_testroot_finder_indirect_{scope}': indirect(scope) for scope in scopes}
    pytester.makepyfile(**indirect_tests)
    pytester.runpytest().assert_outcomes(passed=len(fixtured_tests) + len(indirect_tests))


@pytest.mark.parametrize('value', ['tmp', None])
def test_configuration_parametrized_testroot_prefix(pytester, pytester_source, value):
    prefix = value or ''  # the constructor of TestRootFinder normalizes the prefix
    chk_testroot_finder_with_fixtures(pytester, 'testroot_prefix', 'prefix', value, prefix)


@pytest.mark.parametrize('value', [None, 'default'])
def test_configuration_parametrized_default_testroot(pytester, pytester_source, value):
    chk_testroot_finder_with_fixtures(pytester, 'default_testroot', 'default', value, value)


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
