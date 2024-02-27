from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, TypeVar, final, overload

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from _pytest.pytester import Pytester, RunResult

# delimiters where debug content is printed
PREFIX = '<' * 8
SUFFIX = '>' * 8

T = TypeVar('T')


@final
class _SourceInfo(NamedTuple):
    path: Path
    namespace: str
    env_crc32: int
    srcdir_id: str


def SourceInfo(path: str) -> _SourceInfo:
    abspath = Path(path).absolute()

    namespace = abspath.parent.parent.stem
    try:
        uuid.UUID(namespace, version=5)
    except ValueError:
        pytest.fail(f'cannot extract namespace ID from: {path!r}')

    env_crc32 = abspath.parent.stem
    if not env_crc32 or not env_crc32.isnumeric():
        pytest.fail(f'cannot extract configuration checksum from: {path!r}')

    return _SourceInfo(abspath, namespace, int(env_crc32), abspath.stem)


def send_stmt(name: str, stmt: str) -> str:
    return f"print(f'\\n{PREFIX}{name}={stmt}{SUFFIX}')"


def get_output(pytester: Pytester, *, count: int) -> Output:
    res = pytester.runpytest('--show-capture=no', '-s')
    res.assert_outcomes(passed=count)
    return Output(res)


class Output:
    def __init__(self, res: RunResult) -> None:
        self.res = res
        self.lines = tuple(res.outlines)

    @overload
    def find(self, name: str, pattern: str = ..., *, dtype: None = ...) -> str | None:
        ...

    @overload
    def find(self, name: str, pattern: str = ..., *, dtype: Callable[[str], T]) -> T | None:
        ...

    def find(
        self,
        name: str,
        pattern: str = r'.*',
        *, dtype: Callable[[str], Any] | None = None,
    ) -> Any:
        return next(iter(self.findall(name, pattern, dtype=dtype)), None)

    @overload
    def findall(self, name: str, pattern: str = ..., *, dtype: None = ...) -> Sequence[str]:
        ...

    @overload
    def findall(self, name: str, pattern: str = ..., *, dtype: Callable[[str], T]) -> Sequence[T]:
        ...

    def findall(
        self,
        name: str,
        pattern: str = r'.*',
        *,
        dtype: Callable[[str], Any] | None = None,
    ) -> Sequence[Any]:
        name = re.escape(name)
        p = re.compile(rf'^{PREFIX}{name}=({pattern}){SUFFIX}$')
        matches = filter(None, map(p.match, self.lines))
        values = (m.group(1) for m in matches)
        return tuple(map(dtype, values)) if callable(dtype) else tuple(values)
