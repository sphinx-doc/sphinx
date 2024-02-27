from __future__ import annotations

import uuid

from .util import SourceInfo, get_output, send_stmt


def test_grouped_isolation_no_shared_result(pytester):
    def gen(testid: str) -> str:
        return f'''
import pytest

@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic')
@pytest.mark.isolate('grouped')
def test_group_{testid}(app, value):
    {send_stmt(testid, "{app.srcdir!s}")}
'''

    pytester.makepyfile('\n'.join(map(gen, ('a', 'b'))))
    output = get_output(pytester, count=4)

    srcs_a = output.findall('a', dtype=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert len(set(srcs_a)) == 1

    srcs_b = output.findall('b', dtype=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = srcs_a[0], srcs_b[0]
    assert srcinfo_a.namespace == srcinfo_b.namespace  # same module
    assert srcinfo_a.env_crc32 == srcinfo_b.env_crc32  # same config
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
    {send_stmt(testid, "{app.srcdir!s}")}
'''
    pytester.makepyfile('\n'.join(map(gen, ('a', 'b'))))
    output = get_output(pytester, count=4)

    srcs_a = output.findall('a', dtype=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert len(set(srcs_a)) == 1

    srcs_b = output.findall('b', dtype=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    assert srcs_a[0] == srcs_b[0]


def test_shared_result_different_config(pytester):
    shared_id = uuid.uuid4().hex

    def gen(testid: str) -> str:
        return f'''
import pytest

@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic', confoverrides={{"author": {testid!r}}})
@pytest.mark.test_params(shared_result={shared_id!r})
def test_group_{testid}(app, value):
    {send_stmt(testid, "{app.srcdir!s}")}
'''
    pytester.makepyfile('\n'.join(map(gen, ('a', 'b'))))
    output = get_output(pytester, count=4)

    srcs_a = output.findall('a', dtype=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert len(set(srcs_a)) == 1

    srcs_b = output.findall('b', dtype=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = srcs_a[0], srcs_b[0]
    assert srcinfo_a.namespace == srcinfo_b.namespace  # same module
    assert srcinfo_a.env_crc32 != srcinfo_b.env_crc32  # diff config
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
    {send_stmt(testid, "{app.srcdir!s}")}
'''
    pytester.makepyfile(test_a=gen('a'))
    pytester.makepyfile(test_b=gen('b'))
    output = get_output(pytester, count=4)

    srcs_a = output.findall('a', dtype=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert srcs_a[0] == srcs_a[1]

    srcs_b = output.findall('b', dtype=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = srcs_a[0], srcs_b[0]
    assert srcinfo_a.namespace != srcinfo_b.namespace  # diff module
    assert srcinfo_a.env_crc32 == srcinfo_b.env_crc32  # same config
    assert srcinfo_a.srcdir_id == srcinfo_b.srcdir_id  # same shared id
