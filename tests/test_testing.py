from __future__ import annotations

from enum import IntEnum
from pathlib import Path

import pytest

from sphinx.testing.pytest_util import TestRootFinder


@pytest.mark.parametrize('rootdir', ['/'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/foo'), (None, None)])
def test_testroot_finder(rootdir, name, expect):
    finder = TestRootFinder(rootdir)
    assert finder.find(name) == expect


@pytest.mark.parametrize('default', [None, 'default'])
@pytest.mark.parametrize('prefix', [None, 'test-'])
@pytest.mark.parametrize('name', [None, 'foo'])
def test_testroot_finder_no_rootdir(default, prefix, name):
    finder = TestRootFinder()
    assert finder.find(name) is None


@pytest.mark.parametrize('rootdir', ['/'])
@pytest.mark.parametrize('default', ['default'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/foo'), (None, '/default')])
def test_testroot_finder_with_default(rootdir, default, name, expect):
    finder = TestRootFinder(rootdir, default)
    assert finder.find(name) == expect


@pytest.mark.parametrize('rootdir', ['/'])
@pytest.mark.parametrize('prefix', ['test-'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/test-foo'), (None, None)])
def test_testroot_finder_with_prefix(rootdir, prefix, name, expect):
    finder = TestRootFinder(rootdir, prefix=prefix)
    assert finder.find(name) == expect


@pytest.mark.parametrize('rootdir', ['/'])
@pytest.mark.parametrize('default', ['default'])
@pytest.mark.parametrize('prefix', ['test-'])
@pytest.mark.parametrize(('name', 'expect'), [('foo', '/test-foo'), (None, '/test-default')])
def test_testroot_finder_with_default_and_prefix(rootdir, default, prefix, name, expect):
    finder = TestRootFinder(rootdir, default, prefix)
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


@pytest.mark.parametrize(('sphinx_default_isolation', 'policy'), [
    (None, 'none'), (False, 'none'), (True, 'always'),
    ('none', 'none'), ('once', 'once'), ('always', 'always'),
])
@pytest.mark.sphinx('dummy')
def test_mark_sphinx_with_isolation(app_params, sphinx_default_isolation, policy):
    isolate = app_params.kwargs['isolate']
    assert isinstance(isolate, IntEnum)
    assert isolate.name == policy
