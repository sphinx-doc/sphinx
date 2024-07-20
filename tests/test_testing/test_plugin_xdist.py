from __future__ import annotations

import itertools
import string
from typing import TYPE_CHECKING, NamedTuple

import pytest

from sphinx.testing._internal.util import UID_HEXLEN

from ._const import MAGICO, MAGICO_PLUGIN_NAME, SPHINX_PLUGIN_NAME
from ._util import E2E, SourceInfo

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final, Literal

    from ._util import MagicOutput

    GroupPolicy = Literal['native', 'sphinx', 123]


@pytest.mark.serial
def test_framework_no_xdist(pytester):
    pytester.makepyfile(f"""
from sphinx.testing._internal.pytest_xdist import get_xdist_policy

def test_check_setup(pytestconfig):
    assert pytestconfig.pluginmanager.has_plugin({SPHINX_PLUGIN_NAME!r})
    assert pytestconfig.pluginmanager.has_plugin({MAGICO_PLUGIN_NAME!r})
    assert not pytestconfig.pluginmanager.has_plugin('xdist')
    assert get_xdist_policy(pytestconfig) == 'no'
""")
    assert E2E(pytester).run(passed=1)


@pytest.mark.serial
def test_framework_with_xdist(pytester):
    pytester.makepyfile(f"""
from sphinx.testing._internal.pytest_xdist import get_xdist_policy

def test_check_setup(pytestconfig):
    assert pytestconfig.pluginmanager.has_plugin({SPHINX_PLUGIN_NAME!r})
    assert pytestconfig.pluginmanager.has_plugin({MAGICO_PLUGIN_NAME!r})
    assert pytestconfig.pluginmanager.has_plugin('xdist')
    assert get_xdist_policy(pytestconfig) == 'loadgroup'
""")
    assert E2E(pytester).xdist_run(passed=1)


FOO: Final[str] = 'foo'
BAR: Final[str] = 'bar'
GROUP_POLICIES: Final[Sequence[GroupPolicy]] = ('native', 'sphinx', 123)


def _SRCDIR_VAR(testid):
    return f'sid[{testid}]'


def _NODEID_VAR(testid):
    return f'nid[{testid}]'


def _WORKID_VAR(testid):
    return f'wid[{testid}]'


# common header to write once


_FILEHEADER = r"""
import pytest

@pytest.fixture(autouse=True)
def _add_test_id(request, app_info_extras):
    app_info_extras.update(test_id=request.node.nodeid)

@pytest.fixture()
def value():  # fake fixture that is to be replaced by a parametrization
    return 0
"""


def _casecontent(testid: str, *, group: GroupPolicy, parametrized: bool) -> str:
    if group == 'native':
        # do not use the auto strategy
        xdist_group_mark = '@pytest.mark.no_default_xdist_group()'
    elif group == 'sphinx':
        # use the auto-strategy by Sphinx
        xdist_group_mark = None
    else:
        xdist_group_mark = f'@pytest.mark.xdist_group({str(group)!r})'

    if parametrized:
        parametrize_mark = "@pytest.mark.parametrize('value', [1, 2])"
    else:
        parametrize_mark = None

    marks = '\n'.join(filter(None, (xdist_group_mark, parametrize_mark)))
    return f"""
{marks}
@pytest.mark.sphinx('dummy')
def test_group_{testid}({MAGICO}, request, app, worker_id, value):
    assert request.config.pluginmanager.has_plugin('xdist')
    assert hasattr(request.config, 'workerinput')

    {MAGICO}({_SRCDIR_VAR(testid)!r}, str(app.srcdir))
    {MAGICO}({_NODEID_VAR(testid)!r}, request.node.nodeid)
    {MAGICO}({_WORKID_VAR(testid)!r}, worker_id)
"""


class _ExtractInfo(NamedTuple):
    source: SourceInfo
    """The sources directory information."""

    workid: str
    """The xdist-worker ID."""
    nodeid: str
    """The test node id."""

    @property
    def loader(self) -> str | None:
        """The xdist-group (if any)."""
        parts = self.nodeid.rsplit('@', maxsplit=1)
        assert len(parts) == 2 or parts == [self.nodeid]
        return parts[1] if len(parts) == 2 else None


def _extract_infos(
    output: MagicOutput, name: str, *, parametrized: bool
) -> list[_ExtractInfo]:
    srcs = output.findall(_SRCDIR_VAR(name), t=SourceInfo)
    assert len(srcs) > 1 if parametrized else len(srcs) == 1
    assert all(srcs)

    wids = output.findall(_WORKID_VAR(name))
    assert len(wids) == len(srcs)
    assert all(wids)

    nids = output.findall(_NODEID_VAR(name))
    assert len(nids) == len(srcs)
    assert all(nids)

    return list(itertools.starmap(_ExtractInfo, zip(srcs, wids, nids)))


def _check_parametrized_test_suite(suite: Sequence[_ExtractInfo]) -> None:
    for tx, ty in itertools.combinations(suite, 2):  # type: (_ExtractInfo, _ExtractInfo)
        # sub-tests have different node IDs
        assert tx.nodeid != ty.nodeid
        # With xdist enabled, sub-tests are by default dispatched
        # arbitrarily and may not have the same real path; however
        # their namespace and configuration checksum must match.
        assert tx.source.contnode == ty.source.contnode
        assert tx.source.checksum == ty.source.checksum
        assert tx.source.filename == ty.source.filename

        # the real paths of x and y only differ by their worker id
        assert tx.workid in tx.source.realpath
        x_to_y = tx.source.realpath.replace(tx.workid, ty.workid, 1)
        assert ty.workid in ty.source.realpath
        y_to_x = ty.source.realpath.replace(ty.workid, tx.workid, 1)
        assert x_to_y == ty.source.realpath
        assert y_to_x == tx.source.realpath


def _check_xdist_group(group: GroupPolicy, items: Sequence[_ExtractInfo]) -> None:
    groups = {item.loader for item in items}
    assert len(groups) == 1
    actual_group = groups.pop()

    if group == 'native':
        # no group is specified
        assert actual_group is None
    elif group == 'sphinx':
        # sphinx automatically generates a group using the node location
        assert isinstance(actual_group, str)
        assert set(actual_group).issubset(string.hexdigits)
        assert len(actual_group) == UID_HEXLEN
    else:
        assert isinstance(group, int)
        assert actual_group == str(group)


def _check_same_policy(group: GroupPolicy, suites: Sequence[Sequence[_ExtractInfo]]) -> None:
    suite_loaders = [{item.loader for item in suite} for suite in suites]
    assert all(len(loaders) == 1 for loaders in suite_loaders)
    groups = [loaders.pop() for loaders in suite_loaders]

    if group == 'native':
        for group_name, suite in zip(groups, suites):
            assert group_name is None, suite
    elif group == 'sphinx':
        # the auto-generated groups are different
        # because the tests are at different places
        assert len(set(groups)) == len(groups)
    else:
        for group_name, suite in zip(groups, suites):
            assert group_name == str(group), suite


@pytest.mark.serial
class TestParallelTestingModule:
    @staticmethod
    def run(e2e: E2E, *, parametrized: bool, **groups: GroupPolicy) -> MagicOutput:
        e2e.write(_FILEHEADER)
        for testid, group in groups.items():
            e2e.write(_casecontent(testid, group=group, parametrized=parametrized))
        return e2e.xdist_run(jobs=len(groups))  # ensure to have distinct runners

    @pytest.mark.parametrize('policy', GROUP_POLICIES)
    def test_source_for_non_parmetrized_tests(self, e2e: E2E, policy: GroupPolicy) -> None:
        output = self.run(e2e, **dict.fromkeys((FOO, BAR), policy), parametrized=False)
        foo = _extract_infos(output, FOO, parametrized=False)[0]
        bar = _extract_infos(output, BAR, parametrized=False)[0]

        if policy in {'native', 'sphinx'}:
            # by default, the worker ID will be different, hence
            # the difference of paths
            assert foo.source.realpath != bar.source.realpath
        else:
            # same group *and* same configuration implies (by default)
            # the same sources directory (i.e., no side-effect expected)
            assert foo.source.realpath == bar.source.realpath

        # same module, so same base node
        assert foo.source.contnode == bar.source.contnode
        # same configuration for this minimal test
        assert foo.source.checksum == bar.source.checksum
        # the sources directory name is the same since no isolation is expected
        assert foo.source.filename == bar.source.filename

        # the node IDs are distinct
        assert foo.nodeid != bar.nodeid

        if policy in {'native', 'sphinx'}:
            # the worker IDs are distinct since no xdist group is set
            assert foo.workid != bar.workid
            # for non-parametrized tests, 'native' and 'sphinx' policies
            # are equivalent (i.e., they do not set an xdist group)
            assert foo.loader is None
            assert bar.loader is None
        else:
            # the worker IDs are the same since they have the same group
            group = str(policy)
            assert foo.workid == bar.workid
            assert foo.loader == group
            assert bar.loader == group

    @pytest.mark.parametrize(
        ('foo_group', 'bar_group'),
        [
            *zip(GROUP_POLICIES, GROUP_POLICIES),
            *itertools.combinations(GROUP_POLICIES, 2),
        ],
    )
    def test_source_for_parametrized_tests(
        self,
        e2e: E2E,
        foo_group: GroupPolicy,
        bar_group: GroupPolicy,
    ) -> None:
        output = self.run(e2e, **{FOO: foo_group, BAR: bar_group}, parametrized=True)
        foo = _extract_infos(output, FOO, parametrized=True)
        bar = _extract_infos(output, BAR, parametrized=True)

        _check_parametrized_test_suite(foo)
        _check_parametrized_test_suite(bar)

        tx: _ExtractInfo
        ty: _ExtractInfo

        for tx, ty in itertools.combinations((*foo, *bar), 2):
            # inter-collectors also have the same source info
            # except for the node location (fspath, lineno)
            assert tx.source.contnode == ty.source.contnode
            assert tx.source.checksum == ty.source.checksum
            assert tx.source.filename == ty.source.filename

        _check_xdist_group(foo_group, foo)
        _check_xdist_group(bar_group, bar)

        if (group := foo_group) == bar_group:
            _check_same_policy(group, [foo, bar])


@pytest.mark.serial
class TestParallelTestingPackage:
    """Same as :class:`TestParallelTestingModule` but with tests in different files."""

    @staticmethod
    def run(e2e: E2E, *, parametrized: bool, **groups: GroupPolicy) -> MagicOutput:
        for testid, group in groups.items():
            source = _casecontent(testid, group=group, parametrized=parametrized)
            e2e.write(testid, _FILEHEADER, source)
        return e2e.xdist_run(jobs=len(groups))  # ensure to have distinct runners

    @pytest.mark.parametrize('policy', GROUP_POLICIES)
    def test_source_for_non_parmetrized_tests(self, e2e: E2E, policy: GroupPolicy) -> None:
        output = self.run(e2e, **dict.fromkeys((FOO, BAR), policy), parametrized=False)
        foo = _extract_infos(output, FOO, parametrized=False)[0]
        bar = _extract_infos(output, BAR, parametrized=False)[0]

        # Unlike for the module-scope tests, both the full path
        # and the namespace ID are distinct since they are based
        # on the module name (which is distinct for each suite since
        # they are in different files).
        assert foo.source.realpath != bar.source.realpath
        assert foo.source.contnode != bar.source.contnode

        # logic blow is the same as for module-scoped tests
        assert foo.source.checksum == bar.source.checksum
        assert foo.source.filename == bar.source.filename
        assert foo.nodeid != bar.nodeid

        if policy in {'native', 'sphinx'}:
            assert foo.workid != bar.workid
            assert foo.loader is None
            assert bar.loader is None
        else:
            group = str(policy)
            assert foo.workid == bar.workid
            assert foo.loader == group
            assert bar.loader == group

    @pytest.mark.parametrize(
        ('foo_group', 'bar_group'),
        [
            *zip(GROUP_POLICIES, GROUP_POLICIES),
            *itertools.combinations(GROUP_POLICIES, 2),
        ],
    )
    def test_source_for_parametrized_tests(
        self,
        e2e: E2E,
        foo_group: GroupPolicy,
        bar_group: GroupPolicy,
    ) -> None:
        output = self.run(e2e, **{FOO: foo_group, BAR: bar_group}, parametrized=True)
        foo = _extract_infos(output, FOO, parametrized=True)
        bar = _extract_infos(output, BAR, parametrized=True)

        _check_parametrized_test_suite(foo)
        _check_parametrized_test_suite(bar)

        tx: _ExtractInfo
        ty: _ExtractInfo
        for tx, ty in itertools.product(foo, bar):
            # the base node is distinct since not in the same module (this
            # was already checked previously, but here we check when we mix
            # the policies whereas before we checked with identical policies)
            assert tx.source.contnode != ty.source.contnode
            assert tx.source.checksum == ty.source.checksum
            assert tx.source.filename == ty.source.filename

        _check_xdist_group(foo_group, foo)
        _check_xdist_group(bar_group, bar)

        if (group := foo_group) == bar_group:
            _check_same_policy(group, [foo, bar])
