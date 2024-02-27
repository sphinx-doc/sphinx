from __future__ import annotations

import uuid

import pytest

from .util import SourceInfo, get_output, send_stmt

UNIQUE_ID = uuid.uuid4().hex


@pytest.fixture(autouse=True)
def pytester_source_override(pytester, pytester_source):
    source = pytester_source.read_text('utf-8') + '''
try:
    pytest_plugins = [*pytest_plugins, 'xdist']
except NameError:
    pytest_plugins = ['xdist']

def pytest_load_initial_conftests(args):
    args[:] = ["-n", "4"] + args
'''
    return pytester.makeconftest(source)


def _filecontent(shared_result: str, testid: str, groupid: object = 0) -> str:
    return f'''
import pytest

@pytest.mark.xdist_group('{groupid!r}')
@pytest.mark.sphinx('dummy')
@pytest.mark.test_params(shared_result={shared_result!r})
def test_group_{testid}(app, worker_id):
    # force an output since xdist does not work well with '-s'
    {send_stmt(testid, "{app.srcdir!s}")}
    {send_stmt(f'gw[{testid}]', "{worker_id}")}
'''


def test_parallel_testing_single_file(pytester, pytester_source):
    uid = uuid.uuid4().hex
    pytester.makepyfile('\n'.join(_filecontent(uid, x) for x in ('a', 'b')))
    output = get_output(pytester, count=2)
    src_a = output.find('a')
    assert src_a is not None

    src_b = output.find('b')
    assert src_b is not None

    # executed in the same worker
    assert output.find('gw[a]') is not None
    assert output.find('gw[a]') == output.find('gw[b]')

    # same sources path
    assert src_a == src_b


def test_parallel_testing_multiple_files(pytester, pytester_source):
    uid = uuid.uuid4().hex

    pytester.makepyfile(**{
        'test_group_a/test_a': _filecontent(uid, 'a'),
        'test_group_b/test_b': _filecontent(uid, 'b'),
    })
    output = get_output(pytester, count=2)

    src_a = output.find('a', dtype=SourceInfo)
    assert src_a is not None

    src_b = output.find('b', dtype=SourceInfo)
    assert src_b is not None

    # executed in the same worker
    assert output.find('gw[a]') is not None
    assert output.find('gw[a]') == output.find('gw[b]')

    # executed in the same worker but in different directories
    assert src_a.namespace != src_b.namespace
    assert src_a.env_crc32 == src_b.env_crc32
    assert src_a.srcdir_id == src_b.srcdir_id
