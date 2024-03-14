from __future__ import annotations

import textwrap

import pytest
from _pytest.outcomes import Failed

from ._const import MAGICO


def test_native_pytest_cannot_intercept(pytester):
    pytester.makepyfile(textwrap.dedent('''
        def test_inner_1(): print("YAY")
        def test_inner_2(): print("YAY")
    '''.strip('\n')))

    res = pytester.runpytest('-s', '-n2', '-p', 'xdist')
    res.assert_outcomes(passed=2)

    with pytest.raises(Failed):
        res.stdout.fnmatch_lines_random(["*YAY*"])


@pytest.mark.serial()
def test_magic_buffer_can_intercept_vars(request, e2e):
    e2e.makepyfile(textwrap.dedent(f'''
        def test_inner_1({MAGICO}): 
            {MAGICO}("a", 1)
            {MAGICO}("b", -1)
            {MAGICO}("b", -2)

        def test_inner_2({MAGICO}): 
            {MAGICO}("a", 2)
            {MAGICO}("b", -3)
            {MAGICO}("b", -4)
    '''.strip('\n')))
    output = e2e.xdist_run(passed=2)

    assert sorted(output.findall('a', t=int)) == [1, 2]
    assert sorted(output.findall('b', t=int)) == [-4, -3, -2, -1]

    assert output.find('a', nodeid='*::test_inner_1', t=int) == 1
    assert output.findall('a', nodeid='*::test_inner_1', t=int) == [1]

    assert output.find('b', nodeid='*::test_inner_1', t=int) == -1
    assert output.findall('b', nodeid='*::test_inner_1', t=int) == [-1, -2]

    assert output.find('a', nodeid='*::test_inner_2', t=int) == 2
    assert output.findall('a', nodeid='*::test_inner_2', t=int) == [2]

    assert output.find('b', nodeid='*::test_inner_2', t=int) == -3
    assert output.findall('b', nodeid='*::test_inner_2', t=int) == [-3, -4]


@pytest.mark.serial()
def test_magic_buffer_can_intercept_info(e2e):
    e2e.makepyfile(textwrap.dedent(f'''
        def test_inner_1({MAGICO}): {MAGICO}.info("YAY1")
        def test_inner_2({MAGICO}): {MAGICO}.info("YAY2")
    '''.strip('\n')))
    output = e2e.xdist_run(passed=2)

    assert sorted(output.messages()) == ['YAY1', 'YAY2']
    assert output.message(nodeid='*::test_inner_1') == 'YAY1'
    assert output.message(nodeid='*::test_inner_2') == 'YAY2'


@pytest.mark.serial()
def test_magic_buffer_e2e(e2e):
    e2e.write('file1', textwrap.dedent(f'''
        def test1({MAGICO}):
            {MAGICO}("a", 1)
            {MAGICO}("b", 2.5)
            {MAGICO}("b", 5.8)
    '''.strip('\n')))

    e2e.write('file2', textwrap.dedent(f'''
        def test2({MAGICO}):
            {MAGICO}.info("result is:", 123)
            {MAGICO}.info("another message")
    '''.strip('\n')))

    output = e2e.xdist_run(passed=2)

    assert output.findall('a', t=int) == [1]
    assert output.findall('b', t=float) == [2.5, 5.8]
    assert output.messages() == ["result is: 123", "another message"]
