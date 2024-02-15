"""Sphinx test fixtures for pytest"""

from __future__ import annotations

import os
import uuid
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, TypedDict, cast

import pytest

if TYPE_CHECKING:
    from typing import Any

    from _pytest.nodes import Node


class AppRequiredKeywords(TypedDict):
    srcdir: Path
    testroot: str
    isolated: bool


class AppKeywords(AppRequiredKeywords, total=False):
    freshenv: bool
    confoverrides: dict[str, Any]
    tags: list[str]
    docutils_conf: str
    parallel: int

    status: StringIO
    warning: StringIO


class AppParams(NamedTuple):
    args: list[Any]
    kwargs: AppKeywords


def extract_app_params(
    node: Node,
    test_params: TestParams | None = None,
    session_temp_dir: str | os.PathLike[str] | None = None,
    default_testroot: str | None = None,
) -> tuple[list[Any], AppKeywords]:
    # process pytest.mark.sphinx
    poargs: dict[int, Any] = {}
    kwargs: dict[str, Any] = {}

    # to avoid stacking positional args
    for info in reversed(list(node.iter_markers("sphinx"))):
        poargs |= dict(enumerate(info.args))
        kwargs.update(info.kwargs)

    args = [poargs[i] for i in sorted(poargs.keys())]
    isolated = kwargs.setdefault('isolated', False)
    testroot = kwargs.setdefault('testroot', default_testroot or '')

    # process pytest.mark.test_params
    test_params = test_params or extract_test_params(node)

    if shared_srcdir := test_params['shared_result']:
        if isolated:
            pytest.fail("'shared_result' is mutually exclusive with isolated=True")

        if 'srcdir' in kwargs and kwargs['srcdir'] != shared_srcdir:
            pytest.fail('You can not specify shared_result and srcdir in same time.')

        # force the (common) source directory
        kwargs['srcdir'] = shared_srcdir

    # construct the source directory
    kwargs['srcdir'] = Path(
        session_temp_dir or '',
        kwargs.get('srcdir', testroot),
        uuid.uuid4().hex if isolated else '',
    )
    return args, cast(AppKeywords, kwargs)


class TestParams(TypedDict):
    shared_result: str | None


def extract_test_params(node: Node) -> TestParams:
    env = node.get_closest_marker('test_params')
    kwargs = env.kwargs if env else {}
    result = {'shared_result': None} | kwargs

    if result['shared_result'] and not isinstance(result['shared_result'], str):
        msg = 'You can only provide a string type of value for "shared_result"'
        pytest.fail(msg)
    return cast(TestParams, result)

