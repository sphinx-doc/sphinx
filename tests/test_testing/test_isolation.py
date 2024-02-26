from __future__ import annotations

import contextlib
import os
import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from _pytest.pytester import Pytester, RunResult


class SourceInfo(NamedTuple):
    namespace: str
    cnf_crc32: int
    srcdir_id: str


def _getsrcinfo(path: Path) -> SourceInfo:
    return SourceInfo(
        path.parent.parent.stem,
        int(path.parent.stem),
        path.stem,
    )


def _run(pytester: Pytester, *, passed: int) -> RunResult:
    with (
        open(os.devnull, 'w') as fp,
        contextlib.redirect_stdout(fp),
        contextlib.redirect_stderr(fp),
    ):
        res = pytester.runpytest('-s')
    res.assert_outcomes(passed=passed)
    return res


def _getsrcdirs(lines: list[str], testid: str) -> list[Path]:
    p = re.compile(f'@@{testid}=(.+)$')
    ms = filter(None, map(p.match, lines))
    return [Path(m.group(1)) for m in ms]


def test_grouped_isolation_no_shared_result(pytester):
    def gen(testid: str) -> str:
        return f'''
import pytest
@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic')
@pytest.mark.isolate('grouped')
def test_group_{testid}(app, value):
    print(f'\\n@@{testid}={{app.srcdir!s}}')
'''

    pytester.makepyfile('\n'.join(map(gen, ('a', 'b'))))
    res = _run(pytester, passed=4)

    srcs_a = _getsrcdirs(res.outlines, 'a')
    assert len(set(srcs_a)) == 1
    srcs_b = _getsrcdirs(res.outlines, 'b')
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = _getsrcinfo(srcs_a[0]), _getsrcinfo(srcs_b[0])
    assert srcinfo_a.namespace == srcinfo_b.namespace  # same module
    assert srcinfo_a.cnf_crc32 == srcinfo_b.cnf_crc32  # same config
    assert srcinfo_a.srcdir_id != srcinfo_b.srcdir_id  # diff shared id


def test_shared_result(pytester):
    shared_id = uuid.uuid4().hex

    def gen(testid: str) -> str:
        return f'''
import pytest
@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic')
@pytest.mark.test_params(shared_result={shared_id!r})
def test_group_{testid}(app, value):
    print(f'\\n@@{testid}={{app.srcdir!s}}')
'''
    pytester.makepyfile('\n'.join(map(gen, ('a', 'b'))))
    res = _run(pytester, passed=4)

    srcs_a = _getsrcdirs(res.outlines, 'a')
    assert len(set(srcs_a)) == 1

    srcs_b = _getsrcdirs(res.outlines, 'b')
    assert len(set(srcs_b)) == 1

    assert srcs_a[0] == srcs_b[0]


def test_shared_result_different_config(pytester):
    shared_id = uuid.uuid4().hex

    def gen(testid: str) -> str:
        return f'''
    import pytest
    @pytest.mark.parametrize('value', [1, 2])
    @pytest.mark.sphinx('dummy', testroot='basic',
                        confoverrides={{"author": {testid!r}}})
    @pytest.mark.test_params(shared_result={shared_id!r})
    def test_group_{testid}(app, value):
        print(f'\\n@@{testid}={{app.srcdir!s}}')
    '''
    pytester.makepyfile('\n'.join(map(gen, ('a', 'b'))))
    res = _run(pytester, passed=4)

    srcs_a = _getsrcdirs(res.outlines, 'a')
    assert len(set(srcs_a)) == 1

    srcs_b = _getsrcdirs(res.outlines, 'b')
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = _getsrcinfo(srcs_a[0]), _getsrcinfo(srcs_b[0])
    assert srcinfo_a.namespace == srcinfo_b.namespace  # same module
    assert srcinfo_a.cnf_crc32 != srcinfo_b.cnf_crc32  # diff config
    assert srcinfo_a.srcdir_id == srcinfo_b.srcdir_id  # same shared id


def test_shared_result_different_module(pytester):
    shared_id = uuid.uuid4().hex

    def gen(testid: str) -> str:
        return f'''
import pytest
@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic')
@pytest.mark.test_params(shared_result={shared_id!r})
def test_group_{testid}(app, value):
    print(f'\\n@@{testid}={{app.srcdir!s}}')
'''
    pytester.makepyfile(test_a=gen('a'))
    pytester.makepyfile(test_b=gen('b'))
    res = _run(pytester, passed=4)

    srcs_a = _getsrcdirs(res.outlines, 'a')
    assert len(set(srcs_a)) == 1

    srcs_b = _getsrcdirs(res.outlines, 'b')
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = _getsrcinfo(srcs_a[0]), _getsrcinfo(srcs_b[0])
    assert srcinfo_a.namespace != srcinfo_b.namespace  # diff module
    assert srcinfo_a.cnf_crc32 == srcinfo_b.cnf_crc32  # same config
    assert srcinfo_a.srcdir_id == srcinfo_b.srcdir_id  # same shared id
