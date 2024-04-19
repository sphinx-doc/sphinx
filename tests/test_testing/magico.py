r"""Interception plugin for checking our plugin.

Testing plugins is achieved by :class:`_pytest.pytester.Pytester`. However,
when ``xdist`` is active, capturing support is limited and it is not possible
to print messages inside the tests being tested and check them outside, e.g.::

    import textwrap

    def test_my_plugin(pytester):
        pytester.makepyfile(textwrap.dedent('''
            def test_inner_1(): print("YAY")
            def test_inner_2(): print("YAY")
        '''.strip('\n')))

        # this should capture the output but xdist does not like it!
        res = pytester.runpytest('-s', '-n2', '-p', 'xdist')
        res.assert_outcomes(passed=2)
        res.stdout.fnmatch_lines_random(["*YAY*"])  # this fails!

Nevertheless, it is possible to treat the (non-failure) report sections shown
when using ``-rA`` as "standard output" and parse their content. For instance,
instead of a ``print``, use::

    import textwrap

    from ._const import MAGICO

    def test_my_plugin(e2e):
        e2e.makepyfile(textwrap.dedent(f'''
            def test_inner_1({MAGICO}): {MAGICO}.text("YAY1")
            def test_inner_2({MAGICO}): {MAGICO}.text("YAY2")
        '''.strip('\n')))

        output = e2e.xdist_run(passed=2)
        assert output.messages() == ["YAY1", "YAY2"]

See :mod:`test_magico` for usage and more details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.test_testing._const import MAGICO
from tests.test_testing._util import MagicStream

if TYPE_CHECKING:
    from collections.abc import Iterator

_MAGICAL_KEY: pytest.StashKey[MagicStream] = pytest.StashKey()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item: pytest.Item) -> Iterator[None]:
    """Initialize the magical buffer fixture for the item."""
    item.stash.setdefault(_MAGICAL_KEY, MagicStream())
    yield


@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item: pytest.Item) -> Iterator[None]:
    """Write the magical buffer content as a report section."""
    # teardown of fixtures
    yield
    # now the fixtures have executed their teardowns
    if (magicobject := item.stash.get(_MAGICAL_KEY, None)) is not None:
        magicobject.pytest_runtest_teardown(item)
        del item.stash[_MAGICAL_KEY]


@pytest.fixture(autouse=True, name=MAGICO)
def __magico_sphinx(request: pytest.FixtureRequest) -> MagicStream:  # NoQA: PT005
    # request.node.stash is not typed in pytest
    stash: pytest.Stash = request.node.stash
    return stash.setdefault(_MAGICAL_KEY, MagicStream())
