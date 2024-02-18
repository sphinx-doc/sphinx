from __future__ import annotations

from enum import IntEnum
from pathlib import Path

import pytest

from sphinx.testing.pytest_util import TestRootFinder


def test_configuration(testroot_finder):
    assert isinstance(testroot_finder.rootdir, Path)
    assert testroot_finder.rootdir.name == 'roots'
    assert testroot_finder.default == 'minimal'
    assert testroot_finder.prefix == 'test-'


@pytest.mark.parametrize('rootdir', ['tmp'], indirect=True)
def test_configuration_parametrized_rootdir(testroot_finder, rootdir):
    assert testroot_finder.rootdir == rootdir


@pytest.mark.parametrize('default_testroot', ['foo'], indirect=True)
def test_configuration_parametrized_default_testroot(testroot_finder, default_testroot):
    assert testroot_finder.default == default_testroot


@pytest.mark.parametrize('testroot_prefix', ['my-'], indirect=True)
def test_configuration_parametrized_testroot_prefix(testroot_finder, testroot_prefix):
    assert testroot_finder.prefix == testroot_prefix


@pytest.mark.parametrize('root', [None])
@pytest.mark.parametrize('default', [None, 'default'])
@pytest.mark.parametrize('prefix', [None, 'test-'])
@pytest.mark.parametrize('name', [None, 'foo'])
def test_testroot_finder_no_rootdir(testroot_finder, root, default, prefix, name):
    finder = TestRootFinder(root, prefix, default)
    assert finder.find(name) is None


@pytest.mark.parametrize('root', ['/'])
@pytest.mark.parametrize('default', [None, ''])
@pytest.mark.parametrize('prefix', [None, ''])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/foo'), (None, None)])
def test_testroot_finder_no_default_no_prefix(root, default, prefix, name, expect):
    finder = TestRootFinder(root, prefix, default)
    assert finder.find(name) == expect


@pytest.mark.parametrize('root', ['/'])
@pytest.mark.parametrize('default', ['default'])
@pytest.mark.parametrize('prefix', [None, ''])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/foo'), (None, '/default')])
def test_testroot_finder_with_default(root, default, prefix, name, expect):
    finder = TestRootFinder(root, prefix, default)
    assert finder.find(name) == expect


@pytest.mark.parametrize('root', ['/'])
@pytest.mark.parametrize('default', [None, ''])
@pytest.mark.parametrize('prefix', ['test-'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/test-foo'), (None, None)])
def test_testroot_finder_with_prefix(root, default, prefix, name, expect):
    finder = TestRootFinder(root, prefix, default)
    assert finder.find(name) == expect


@pytest.mark.parametrize('root', ['/'])
@pytest.mark.parametrize('default', ['default'])
@pytest.mark.parametrize('prefix', ['test-'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/test-foo'), (None, '/test-default')])
def test_testroot_finder(root, default, prefix, name, expect):
    finder = TestRootFinder(root, prefix, default)
    assert finder.find(name) == expect


@pytest.mark.sphinx()
def test_mark_sphinx_use_default_builder(app_params):
    args, kwargs = app_params
    assert not args
    assert kwargs['buildername'] == 'html'


@pytest.mark.sphinx('dummy')
def test_mark_sphinx_with_builder(app_params):
    args, kwargs = app_params
    assert not args

    _sphinx_testroot_path = kwargs['_sphinx_testroot_path']
    assert _sphinx_testroot_path is None or isinstance(_sphinx_testroot_path, str)
    assert not kwargs['_sphinx_shared_result']

    assert kwargs['buildername'] == 'dummy'
    assert kwargs['testroot'] is None or isinstance(kwargs['testroot'], str)
    assert isinstance(kwargs['srcdir'], Path)


@pytest.mark.parametrize(('sphinx_isolation', 'policy'), [
    (None, 'none'), (False, 'none'), (True, 'always'),
    ('none', 'none'), ('once', 'once'), ('always', 'always'),
])
@pytest.mark.sphinx('dummy')
def test_mark_sphinx_with_isolation(app_params, sphinx_isolation, policy):
    isolate = app_params.kwargs['isolate']
    assert isinstance(isolate, IntEnum)
    assert isolate.name == policy
