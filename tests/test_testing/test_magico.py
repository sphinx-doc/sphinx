from __future__ import annotations

import itertools
import os
import textwrap

import pytest
from _pytest.outcomes import Failed

from ._const import MAGICO

import tests.test_testing._util as util
from tests.test_testing._util import CAPTURE_STATE, END_TAG, STOPLINE, TXT_TAG


def test_native_pytest_cannot_intercept(pytester):
    # fmt: off
    pytester.makepyfile(textwrap.dedent('''
        def test_inner_1(): print("YAY")
        def test_inner_2(): print("YAY")
    '''.strip('\n')))
    # fmt: on

    res = pytester.runpytest('-s', '-n2', '-p', 'xdist')
    res.assert_outcomes(passed=2)

    with pytest.raises(Failed):
        res.stdout.fnmatch_lines_random(['*YAY*'])


@pytest.mark.serial()
def test_magic_buffer_can_intercept_vars(request, e2e):
    # fmt: off
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
    # fmt: on
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
    # fmt: off
    e2e.makepyfile(textwrap.dedent(f'''
        def test_inner_1({MAGICO}): {MAGICO}.info("YAY1")
        def test_inner_2({MAGICO}): {MAGICO}.info("YAY2")
    '''.strip('\n')))
    # fmt: on
    output = e2e.xdist_run(passed=2)

    assert sorted(output.messages()) == ['YAY1', 'YAY2']
    assert output.message(nodeid='*::test_inner_1') == 'YAY1'
    assert output.message(nodeid='*::test_inner_2') == 'YAY2'


@pytest.mark.serial()
def test_magic_buffer_e2e(e2e):
    # fmt: off
    e2e.write('file1', textwrap.dedent(f'''
        def test1({MAGICO}):
            {MAGICO}("a", 1)
            {MAGICO}("b", 2.5)
            {MAGICO}("b", 5.8)
    '''.strip('\n')))
    # fmt: on

    # fmt: off
    e2e.write('file2', textwrap.dedent(f'''
        def test2({MAGICO}):
            {MAGICO}.info("result is:", 123)
            {MAGICO}.info("another message")
    '''.strip('\n')))
    # fmt: on

    output = e2e.xdist_run(passed=2)

    assert output.findall('a', t=int) == [1]
    assert output.findall('b', t=float) == [2.5, 5.8]
    assert output.messages() == ['result is: 123', 'another message']


class TestTeardownSectionParser:
    value_channel = os.urandom(4).hex()
    print_channel = os.urandom(4).hex()

    @classmethod
    def new_value_section(cls, nodeid: str) -> list[str]:
        return [
            f'{util.magic_section(nodeid, cls.value_channel, TXT_TAG)} {CAPTURE_STATE}',
            util.format_message_for_value_channel(f'{nodeid}.x', 1, end=''),
            util.format_message_for_value_channel(f'{nodeid}.y', 2, end=''),
            f'{util.magic_section(nodeid, cls.value_channel, END_TAG)} {CAPTURE_STATE}',
            STOPLINE,
        ]

    @classmethod
    def new_print_section(cls, nodeid: str) -> list[str]:
        return [
            f'{util.magic_section(nodeid, cls.print_channel, TXT_TAG)} {CAPTURE_STATE}',
            util.format_message_for_print_channel('some message for', nodeid, end=''),
            util.format_message_for_print_channel(f'{nodeid}.value:', 2, end=''),
            f'{util.magic_section(nodeid, cls.print_channel, END_TAG)} {CAPTURE_STATE}',
            STOPLINE,
        ]

    @pytest.fixture()
    def lines(cls) -> list[str]:
        # fmt: off
        return list(itertools.chain.from_iterable((
            cls.new_value_section('test_a'),
            cls.new_print_section('test_a'),
            cls.new_value_section('test_b'),
        )))
        # fmt: on

    def test_find_teardown_section(self, lines):
        res = util.find_teardown_section(lines, 'test_a', self.value_channel)
        assert res == [
            '<sphinx-magic::value> test_a.x=1',
            '<sphinx-magic::value> test_a.y=2',
        ]

        res = util.find_teardown_section(lines, 'test_a', self.print_channel)
        assert res == [
            '<sphinx-magic::print> some message for test_a',
            '<sphinx-magic::print> test_a.value: 2',
        ]

    def test_find_teardown_sections(self, lines):
        res = util.find_teardown_sections(lines, self.value_channel)
        assert res == {
            'test_a': ['<sphinx-magic::value> test_a.x=1', '<sphinx-magic::value> test_a.y=2'],
            'test_b': ['<sphinx-magic::value> test_b.x=1', '<sphinx-magic::value> test_b.y=2'],
        }

        res = util.find_teardown_sections(lines, self.print_channel)
        assert res == {
            'test_a': [
                '<sphinx-magic::print> some message for test_a',
                '<sphinx-magic::print> test_a.value: 2',
            ],
        }
