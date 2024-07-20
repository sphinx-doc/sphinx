from __future__ import annotations

import uuid

import pytest

from ._const import MAGICO
from ._util import SourceInfo


@pytest.fixture
def random_uuid() -> str:
    return uuid.uuid4().hex


def test_grouped_isolation_no_shared_result(e2e):
    def gen(testid: str) -> str:
        return f"""
@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic')
@pytest.mark.isolate('grouped')
def test_group_{testid}({MAGICO}, app, value):
    {MAGICO}({testid!r}, str(app.srcdir))
"""

    e2e.write(['import pytest', gen('a'), gen('b')])

    output = e2e.run()

    srcs_a = output.findall('a', t=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert len(set(srcs_a)) == 1

    srcs_b = output.findall('b', t=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = srcs_a[0], srcs_b[0]
    assert srcinfo_a.contnode == srcinfo_b.contnode  # same namespace
    assert srcinfo_a.checksum == srcinfo_b.checksum  # same config
    assert srcinfo_a.filename != srcinfo_b.filename  # diff shared id


def test_shared_result(e2e, random_uuid):
    def gen(testid: str) -> str:
        return f"""
@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic')
@pytest.mark.test_params(shared_result={random_uuid!r})
def test_group_{testid}({MAGICO}, app, value):
    {MAGICO}({testid!r}, str(app.srcdir))
"""

    e2e.write('import pytest')
    e2e.write(gen('a'))
    e2e.write(gen('b'))
    output = e2e.run()

    srcs_a = output.findall('a', t=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert len(set(srcs_a)) == 1

    srcs_b = output.findall('b', t=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    assert srcs_a[0] == srcs_b[0]


def test_shared_result_different_config(e2e, random_uuid):
    def gen(testid: str) -> str:
        return f"""
@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic', confoverrides={{"author": {testid!r}}})
@pytest.mark.test_params(shared_result={random_uuid!r})
def test_group_{testid}({MAGICO}, app, value):
    {MAGICO}({testid!r}, str(app.srcdir))
"""

    e2e.write('import pytest')
    e2e.write(gen('a'))
    e2e.write(gen('b'))
    output = e2e.run()

    srcs_a = output.findall('a', t=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert len(set(srcs_a)) == 1

    srcs_b = output.findall('b', t=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = srcs_a[0], srcs_b[0]
    assert srcinfo_a.contnode == srcinfo_b.contnode  # same namespace
    assert srcinfo_a.checksum != srcinfo_b.checksum  # diff config
    assert srcinfo_a.filename == srcinfo_b.filename  # same shared id


def test_shared_result_different_module(e2e, random_uuid):
    def gen(testid: str) -> str:
        return f"""
import pytest

@pytest.mark.parametrize('value', [1, 2])
@pytest.mark.sphinx('dummy', testroot='basic')
@pytest.mark.test_params(shared_result={random_uuid!r})
def test_group_{testid}({MAGICO}, app, value):
    {MAGICO}({testid!r}, str(app.srcdir))
"""

    e2e.makepytest(a=gen('a'), b=gen('b'))
    output = e2e.run()

    srcs_a = output.findall('a', t=SourceInfo)
    assert len(srcs_a) == 2  # two sub-tests
    assert srcs_a[0] == srcs_a[1]

    srcs_b = output.findall('b', t=SourceInfo)
    assert len(srcs_b) == 2  # two sub-tests
    assert len(set(srcs_b)) == 1

    srcinfo_a, srcinfo_b = srcs_a[0], srcs_b[0]
    assert srcinfo_a.contnode != srcinfo_b.contnode  # diff namespace
    assert srcinfo_a.checksum == srcinfo_b.checksum  # same config
    assert srcinfo_a.filename == srcinfo_b.filename  # same shared id
