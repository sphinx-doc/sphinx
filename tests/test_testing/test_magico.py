from __future__ import annotations

import itertools
import textwrap
from typing import TYPE_CHECKING

import pytest
from _pytest.outcomes import Failed

from ._const import MAGICO

from tests.test_testing._util import DataFinder, DataWriter, TextFinder, TextWriter

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tests.test_testing._util import _MagicFinder


def test_native_pytest_cannot_intercept(pytester):
    pytester.makepyfile("""
def test_inner_1(): print("YAY")
def test_inner_2(): print("YAY")
""")

    res = pytester.runpytest('-s', '-n2', '-p', 'xdist')
    res.assert_outcomes(passed=2)

    with pytest.raises(Failed):
        res.stdout.fnmatch_lines_random(['*YAY*'])


@pytest.mark.serial()
def test_magic_buffer_can_intercept_vars(request, e2e):
    e2e.makepyfile(f"""
def test_inner_1({MAGICO}):
    {MAGICO}("a", 1)
    {MAGICO}("b", -1)
    {MAGICO}("b", -2)

def test_inner_2({MAGICO}):
    {MAGICO}("a", 2)
    {MAGICO}("b", -3)
    {MAGICO}("b", -4)
""")
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
    e2e.makepyfile(f"""
def test_inner_1({MAGICO}): {MAGICO}.text("YAY1")
def test_inner_2({MAGICO}): {MAGICO}.text("YAY2")
""")
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
            {MAGICO}.text("result is:", 123)
            {MAGICO}.text("another message")
    '''.strip('\n')))
    # fmt: on

    output = e2e.xdist_run(passed=2)

    assert output.findall('a', t=int) == [1]
    assert output.findall('b', t=float) == [2.5, 5.8]
    assert output.messages() == ['result is: 123', 'another message']


class TestTeardownSectionParser:
    @classmethod
    def new_value_section(cls, nodeid: str) -> Sequence[str]:
        writer = DataWriter()
        writer.write('x', 1, namespace=nodeid)
        writer.write('y', 2, namespace=nodeid)
        return writer.lines(nodeid)

    @classmethod
    def new_print_section(cls, nodeid: str) -> Sequence[str]:
        writer = TextWriter()
        writer.write('some message for', nodeid)
        writer.write(f'{nodeid}.value:', 2)
        return writer.lines(nodeid)

    @pytest.fixture()
    def lines(cls) -> list[str]:
        return [
            *itertools.chain.from_iterable((
                cls.new_value_section('test_a'),
                cls.new_print_section('test_a'),
                cls.new_value_section('test_b'),
            ))
        ]

    @pytest.mark.parametrize(
        ('finder', 'nodeid', 'expect'),
        [
            (
                DataFinder,
                'test_a',
                ['<sphinx-magic::data> test_a.x=1', '<sphinx-magic::data> test_a.y=2'],
            ),
            (
                TextFinder,
                'test_a',
                [
                    '<sphinx-magic::text> some message for test_a',
                    '<sphinx-magic::text> test_a.value: 2',
                ],
            ),
        ],
    )
    def test_find_teardown_section(
        self, finder: type[_MagicFinder], nodeid: str, lines: list[str], expect: list[str]
    ) -> None:
        actual = finder.find_teardown_section(lines, nodeid=nodeid)
        assert actual == expect

    @pytest.mark.parametrize(
        ('finder', 'expect'),
        [
            (
                DataFinder,
                {
                    'test_a': [
                        '<sphinx-magic::data> test_a.x=1',
                        '<sphinx-magic::data> test_a.y=2',
                    ],
                    'test_b': [
                        '<sphinx-magic::data> test_b.x=1',
                        '<sphinx-magic::data> test_b.y=2',
                    ],
                },
            ),
            (
                TextFinder,
                {
                    'test_a': [
                        '<sphinx-magic::text> some message for test_a',
                        '<sphinx-magic::text> test_a.value: 2',
                    ]
                },
            ),
        ],
    )
    def test_find_teardown_sections(
        self, finder: type[_MagicFinder], lines: list[str], expect: dict[str, list[str]]
    ) -> None:
        actual = finder.find_teardown_sections(lines)
        assert actual == expect
