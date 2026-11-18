"""Tests sphinx.util.parallel functions."""

from __future__ import annotations

import os

import pytest

from sphinx.util.parallel import ParallelTasks


class _CallbackError(Exception):
    pass


@pytest.mark.xfail(
    os.name != 'posix',
    reason='Parallel mode does not work on Windows',
)
def test_result_func_error_is_propagated() -> None:
    def result_func(arg: object, result: object) -> None:
        raise _CallbackError

    tasks = ParallelTasks(1)
    tasks.add_task(lambda: None, result_func=result_func)
    with pytest.raises(_CallbackError):
        tasks.join()
