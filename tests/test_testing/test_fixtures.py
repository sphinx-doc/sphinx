from __future__ import annotations

import uuid
from enum import IntEnum
from pathlib import Path

import pytest

from sphinx.testing.pytest_util import pytest_not_raises


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
    assert not kwargs['shared_result']

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


@pytest.mark.sphinx('dummy')
@pytest.mark.test_params(shared_result=uuid.uuid4().hex)
def test_mark_sphinx_with_shared_result(app_params):
    shared_result = app_params.kwargs['shared_result']
    assert shared_result is not None

    srcdir = app_params.kwargs['srcdir']
    assert srcdir.name == shared_result

    with pytest_not_raises(ValueError):
        uuid.UUID(hex=shared_result, version=4)
