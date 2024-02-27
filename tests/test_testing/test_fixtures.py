from __future__ import annotations

from enum import IntEnum
from pathlib import Path

import pytest


@pytest.mark.sphinx()
def test_mark_sphinx_use_default_builder(app_params):
    args, kwargs = app_params
    assert not args
    assert kwargs['buildername'] == 'html'


@pytest.mark.sphinx('dummy')
def test_mark_sphinx_with_builder(app_params):
    args, kwargs = app_params
    assert not args

    testroot_path = kwargs['testroot_path']
    assert testroot_path is None or isinstance(testroot_path, str)
    assert kwargs['shared_result'] is None

    assert kwargs['buildername'] == 'dummy'
    assert kwargs['testroot'] == 'minimal'
    assert isinstance(kwargs['srcdir'], Path)
    assert kwargs['srcdir'].name == 'minimal'


@pytest.mark.parametrize(('sphinx_isolation', 'policy'), [
    (None, 'minimal'), (False, 'minimal'), (True, 'always'),
    ('minimal', 'minimal'), ('grouped', 'grouped'), ('always', 'always'),
])
@pytest.mark.sphinx('dummy')
def test_mark_sphinx_with_isolation(app_params, sphinx_isolation, policy):
    isolate = app_params.kwargs['isolate']
    assert isinstance(isolate, IntEnum)
    assert isolate.name == policy


@pytest.mark.sphinx('dummy')
@pytest.mark.test_params(shared_result='foo')
def test_mark_sphinx_with_shared_result(app_params):
    shared_result = app_params.kwargs['shared_result']
    assert shared_result == 'foo'

    srcdir = app_params.kwargs['srcdir']
    assert srcdir.name == 'minimal-foo'
