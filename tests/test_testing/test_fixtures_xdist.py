from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest

UNIQUE_ID = uuid.uuid4().hex


@pytest.fixture(autouse=True)
def pytester_source_override(pytester, pytester_source):
    source = pytester_source.read_text('utf-8') + '''
try:
    pytest_plugins = [*pytest_plugins, 'xdist']
except NameError:
    pytest_plugins = ['xdist']
'''
    # TODO(picnixz): add -n8 auto
    return pytester.makeconftest(source)


def _filecontent(shared_result: str, testid: str, groupid: object = 0) -> str:
    # xdist does not work well with '-s' so we hack the output by making it fail
    return f'''
@pytest.mark.xdist_group('{groupid!r}')
@pytest.mark.sphinx('dummy')
@pytest.mark.test_params(shared_result={shared_result!r})
def test_group_{testid}(app, shared_result):
    assert 0, f"{testid}={{os.fsdecode(app.srcdir)}}"
'''


def _getsrcdir(lines: list[str], testid: str) -> Path:
    s = next((line for line in lines if f'AssertionError: {testid}=' in line), None)
    assert s is not None
    m = re.search(rf'\bAssertionError: {testid}=(.+)$', s)
    assert m is not None, s
    return Path(m.group(1))


def test_parallel_testing_single_file(pytester, pytester_source):
    uid = uuid.uuid4().hex
    # re-add the 'xdist' plugin
    pytester.makepyfile(f'''
import os

import pytest
{_filecontent(uid, 'a')}
{_filecontent(uid, 'b')}
''')
    res = pytester.runpytest('-n8')
    res.assert_outcomes(failed=2)

    src_a = _getsrcdir(res.outlines, 'a')
    src_b = _getsrcdir(res.outlines, 'b')
    assert src_a.name == src_b.name


def test_parallel_testing_multiple_files(pytester, pytester_source):
    uid = uuid.uuid4().hex
    # re-add the 'xdist' plugin
    pytester.makepyfile(test_a=f'''
import os

import pytest
{_filecontent(uid, 'a')}
''')
    pytester.makepyfile(test_b=f'''
import os

import pytest
{_filecontent(uid, 'b')}
''')
    res = pytester.runpytest('-n8')
    res.assert_outcomes(failed=2)

    src_a = _getsrcdir(res.outlines, 'a')
    src_b = _getsrcdir(res.outlines, 'b')
    assert src_a.name == src_b.name
