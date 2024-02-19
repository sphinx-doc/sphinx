"""Sphinx test suite utilities"""

from __future__ import annotations

__all__ = [
    'assert_node',
    'etree_parse',
    'strip_escseq',
    'SphinxTestApp',
    'SphinxTestAppLazyBuild',
    'SphinxTestAppWrapperForSkipBuilding',
]

import contextlib
import os
import re
import sys
import warnings
from io import StringIO
from types import MappingProxyType
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from docutils import nodes
from docutils.parsers.rst import directives, roles

import sphinx.application
import sphinx.locale
import sphinx.pycode
from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.locale import __
from sphinx.util.docutils import additional_nodes

if TYPE_CHECKING:
    from pathlib import Path

    from docutils.nodes import Node


def assert_node(node: Node, cls: Any = None, xpath: str = "", **kwargs: Any) -> None:
    if cls:
        if isinstance(cls, list):
            assert_node(node, cls[0], xpath=xpath, **kwargs)
            if cls[1:]:
                if isinstance(cls[1], tuple):
                    assert_node(node, cls[1], xpath=xpath, **kwargs)
                else:
                    assert isinstance(node, nodes.Element), \
                        'The node%s does not have any children' % xpath
                    assert len(node) == 1, \
                        'The node%s has %d child nodes, not one' % (xpath, len(node))
                    assert_node(node[0], cls[1:], xpath=xpath + "[0]", **kwargs)
        elif isinstance(cls, tuple):
            assert isinstance(node, (list, nodes.Element)), \
                'The node%s does not have any items' % xpath
            assert len(node) == len(cls), \
                'The node%s has %d child nodes, not %r' % (xpath, len(node), len(cls))
            for i, nodecls in enumerate(cls):
                path = xpath + "[%d]" % i
                assert_node(node[i], nodecls, xpath=path, **kwargs)
        elif isinstance(cls, str):
            assert node == cls, f'The node {xpath!r} is not {cls!r}: {node!r}'
        else:
            assert isinstance(node, cls), \
                f'The node{xpath} is not subclass of {cls!r}: {node!r}'

    if kwargs:
        assert isinstance(node, nodes.Element), \
            'The node%s does not have any attributes' % xpath

        for key, value in kwargs.items():
            if key not in node:
                if (key := key.replace('_', '-')) not in node:
                    msg = f'The node{xpath} does not have {key!r} attribute: {node!r}'
                    raise AssertionError(msg)
            assert node[key] == value, \
                f'The node{xpath}[{key}] is not {value!r}: {node[key]!r}'


def etree_parse(path: str) -> Any:
    with warnings.catch_warnings(record=False):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return ElementTree.parse(path)  # NoQA: S314  # using known data in tests


def strip_escseq(text: str) -> str:
    return re.sub('\x1b.*?m', '', text)


class SphinxTestApp(sphinx.application.Sphinx):
    """A subclass of :class:`~sphinx.application.Sphinx` for tests.

    The constructor uses some better default values for the initialization
    parameters and supports arbitrary keywords stored in the :attr:`extras`
    read-only mapping.

    It is recommended to use::

        @pytest.mark.sphinx('html')
        def test(app):
            app = ...

    instead of::

        def test():
            app = SphinxTestApp('html', srcdir=srcdir)

    In the former case, the 'app' fixture takes care of setting the source
    directory, whereas in the latter, the user must provide it themselves.
    """

    def __init__(
        self,
        buildername: str = 'html',
        *,
        srcdir: Path,
        confoverrides: dict[str, Any] | None = None,
        status: StringIO | None = None,
        warning: StringIO | None = None,
        freshenv: bool = False,
        warningiserror: bool = False,
        tags: list[str] | None = None,
        verbosity: int = 0,
        parallel: int = 0,
        keep_going: bool = False,
        # extra constructor arguments
        builddir: Path | None = None,
        docutils_conf: str | None = None,
        # unknown keyword arguments
        **extras: Any,
    ) -> None:
        if status is None:
            # ensure that :attr:`status` is a StringIO and not sys.stdout
            status = StringIO()
        elif not isinstance(status, StringIO):
            err = __("%r must be a io.StringIO object, got: %s") % ('status', type(status))
            raise TypeError(err)

        if warning is None:
            # ensure that :attr:`warning` is a StringIO and not sys.stdout
            warning = StringIO()
        elif not isinstance(warning, StringIO):
            err = __("%r must be a io.StringIO object, got: %s") % ('warning', type(warning))
            raise TypeError(err)

        self.docutils_conf_path = srcdir / 'docutils.conf'
        if docutils_conf is not None:
            self.docutils_conf_path.write_text(docutils_conf, encoding='utf8')

        if builddir is None:
            builddir = srcdir / '_build'

        confdir = srcdir
        # build directory configuration
        outdir = builddir / buildername
        outdir.mkdir(parents=True, exist_ok=True)
        doctreedir = builddir / 'doctrees'
        doctreedir.mkdir(parents=True, exist_ok=True)
        if confoverrides is None:
            confoverrides = {}

        self._saved_path = sys.path.copy()
        self.extras = MappingProxyType(extras)

        try:
            super().__init__(
                srcdir, confdir, outdir, doctreedir, buildername,
                confoverrides=confoverrides, status=status, warning=warning,
                freshenv=freshenv, warningiserror=warningiserror, tags=tags,
                verbosity=verbosity, parallel=parallel, keep_going=keep_going,
                pdb=False,
            )
        except Exception:
            self.cleanup()
            raise

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} buildername={self.builder.name!r}>'

    @property
    def status(self) -> StringIO:
        """The in-memory I/O for the application status messages."""
        assert isinstance(self._status, StringIO)
        return self._status

    @property
    def warning(self) -> StringIO:
        """The in-memory text I/O for the application warning messages."""
        assert isinstance(self._warning, StringIO)
        return self._warning

    def cleanup(self, doctrees: bool = False) -> None:
        sys.path[:] = self._saved_path
        _clean_up_global_state()
        with contextlib.suppress(FileNotFoundError):
            os.remove(self.docutils_conf_path)

    def build(self, force_all: bool = False, filenames: list[str] | None = None) -> None:
        # TODO(picnixz): remove when #11474 is fixed
        self.env._pickled_doctree_cache.clear()
        super().build(force_all, filenames)


class SphinxTestAppLazyBuild(SphinxTestApp):
    """Class to speed-up tests with common resources.

    This class is used to speed up the test by skipping calls
    to ``app.build()`` if it has already been built and there
    are any output files.
    """

    def build(self, force_all: bool = False, filenames: list[str] | None = None) -> None:
        # see: https://docs.python.org/3/library/os.html#os.scandir
        with os.scandir(self.outdir) as it:
            has_files = next(it, None) is not None

        if not has_files:  # build if no files were already built
            super().build(force_all=force_all, filenames=filenames)


class SphinxTestAppWrapperForSkipBuilding:  # for backward compatibility
    def __init__(self, app_: SphinxTestApp) -> None:
        warnings.warn(
            f'{self.__class__.__name__!r} is deprecated, use '
            f'{SphinxTestAppLazyBuild.__name__!r} instead',
            category=RemovedInSphinx90Warning, stacklevel=2,
        )
        self.app = app_

    def __getattr__(self, name: str) -> Any:
        return getattr(self.app, name)

    def build(self, *args: Any, **kwargs: Any) -> None:
        if not os.listdir(self.app.outdir):
            # if listdir is empty, do build.
            self.app.build(*args, **kwargs)
            # otherwise, we can use built cache


def _clean_up_global_state() -> None:
    # clean up Docutils global state
    directives._directives.clear()  # type: ignore[attr-defined]
    roles._roles.clear()  # type: ignore[attr-defined]
    for node in additional_nodes:
        delattr(nodes.GenericNodeVisitor, f'visit_{node.__name__}')
        delattr(nodes.GenericNodeVisitor, f'depart_{node.__name__}')
        delattr(nodes.SparseNodeVisitor, f'visit_{node.__name__}')
        delattr(nodes.SparseNodeVisitor, f'depart_{node.__name__}')
    additional_nodes.clear()

    # clean up Sphinx global state
    sphinx.locale.translators.clear()

    # clean up autodoc global state
    sphinx.pycode.ModuleAnalyzer.cache.clear()
