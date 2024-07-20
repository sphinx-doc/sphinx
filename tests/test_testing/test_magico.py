from __future__ import annotations

import itertools
import re
from typing import TYPE_CHECKING

import pytest
from _pytest.outcomes import Failed

from tests.test_testing._const import MAGICO
from tests.test_testing._util import DataFinder, DataWriter, TextFinder, TextWriter

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from tests.test_testing._util import MagicFinder, MagicWriter


def test_native_pytest_cannot_intercept(pytester):
    pytester.makepyfile("""
def test_print_1(): print("YAY")
def test_print_2(): print("YAY")
""")

    res = pytester.runpytest('-s', '-n2', '-p', 'xdist')
    res.assert_outcomes(passed=2)

    with pytest.raises(Failed):
        res.stdout.fnmatch_lines_random(['*YAY*'])


@pytest.mark.serial
def test_magic_buffer_can_intercept_data(request, e2e):
    e2e.makepyfile(f"""
def test_data_1({MAGICO}):
    {MAGICO}("a", 1)
    {MAGICO}("b", -1)
    {MAGICO}("b", -2)

def test_data_2({MAGICO}):
    {MAGICO}("a", 2)
    {MAGICO}("b", -3)
    {MAGICO}("b", -4)
""")
    output = e2e.xdist_run(passed=2)

    assert sorted(output.findall('a', t=int)) == [1, 2]
    assert sorted(output.findall('b', t=int)) == [-4, -3, -2, -1]

    assert output.find('a', nodeid='*::test_data_1', t=int) == 1
    assert output.findall('a', nodeid='*::test_data_1', t=int) == [1]

    assert output.find('b', nodeid='*::test_data_1', t=int) == -1
    assert output.findall('b', nodeid='*::test_data_1', t=int) == [-1, -2]

    assert output.find('a', nodeid='*::test_data_2', t=int) == 2
    assert output.findall('a', nodeid='*::test_data_2', t=int) == [2]

    assert output.find('b', nodeid='*::test_data_2', t=int) == -3
    assert output.findall('b', nodeid='*::test_data_2', t=int) == [-3, -4]


@pytest.mark.serial
def test_magic_buffer_can_intercept_text(e2e):
    e2e.makepyfile(f"""
def test_text_1({MAGICO}): {MAGICO}.text("YAY1")
def test_text_2({MAGICO}): {MAGICO}.text("YAY2")
""")
    output = e2e.xdist_run(passed=2)

    assert sorted(output.messages()) == ['YAY1', 'YAY2']
    assert output.message(nodeid='*::test_text_1') == 'YAY1'
    assert output.message(nodeid='*::test_text_2') == 'YAY2'


@pytest.mark.serial
def test_magic_buffer_e2e(e2e):
    TEST_DUMP_DATA = f"""
def test_data({MAGICO}):
    {MAGICO}("a", 1)
    {MAGICO}("b", 2.5)
    {MAGICO}("b", 5.8)
""".strip('\n')
    e2e.write('dump_data', TEST_DUMP_DATA)

    TEST_DUMP_TEXT = f"""
def test_text({MAGICO}):
    {MAGICO}.text("result is:", 123)
    {MAGICO}.text("another message")
""".strip('\n')
    e2e.write('dump_text', TEST_DUMP_TEXT)

    output = e2e.xdist_run(passed=2)

    assert output.findall('a', t=int) == [1]
    assert output.findall('b', t=float) == [2.5, 5.8]
    assert output.messages() == ['result is: 123', 'another message']


class TestTeardownSectionParser:
    @pytest.fixture
    def lines(cls) -> list[str]:
        def data(nodeid: str) -> Sequence[str]:
            writer = DataWriter()
            writer.write('x', 1, namespace=nodeid)
            writer.write('y', 2, namespace=nodeid)
            return writer.lines(nodeid)

        def text(nodeid: str) -> Sequence[str]:
            writer = TextWriter()
            writer.write('some message for', nodeid)
            writer.write(f'{nodeid}.value', 2, sep=': ')
            return writer.lines(nodeid)

        return list(itertools.chain(data('test_a'), text('test_a'), data('test_b')))

    @pytest.mark.parametrize(
        ('finder', 'nodeid', 'expect'),
        [
            (
                DataFinder,
                'test_a',
                [
                    '<sphinx-magic::data> test_a.x=1',
                    '<sphinx-magic::data> test_a.y=2',
                ],
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
        self, finder: type[MagicFinder], nodeid: str, lines: list[str], expect: list[str]
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
        self, finder: type[MagicFinder], lines: list[str], expect: dict[str, list[str]]
    ) -> None:
        actual = finder.find_teardown_sections(lines)
        assert actual == expect

    @pytest.mark.parametrize(
        ('writer_class', 'finder_class', 'write_args', 'error'),
        [
            (DataWriter, DataFinder, [('a', 1), ('b', 2)], TextWriter.format(2)),
            (
                TextWriter,
                TextFinder,
                [('first', 'message'), ('second message',)],
                DataWriter.format('a', 0),
            ),
        ],
    )
    def test_bad_data_block(
        self,
        writer_class: type[MagicWriter],
        finder_class: type[MagicFinder],
        write_args: list[tuple[Any, ...]],
        error: str,
    ) -> None:
        writer = writer_class()
        for args in write_args:
            writer.write(*args)
        writer.writeline(error)

        offset = 1 + len(write_args)
        match = re.escape(f'L:{offset}: invalid line: {error!r}')
        with pytest.raises(AssertionError, match=match):
            finder_class.find_teardown_sections(writer.lines('test'))
