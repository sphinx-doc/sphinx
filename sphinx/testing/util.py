"""
    sphinx.testing.util
    ~~~~~~~~~~~~~~~~~~~

    Sphinx test suite utilities

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import re
import sys
import warnings
from typing import Any, Dict, Generator, IO, List, Pattern
from xml.etree import ElementTree

from docutils import nodes
from docutils.parsers.rst import directives, roles

from sphinx import application, locale
from sphinx.builders.latex import LaTeXBuilder
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.pycode import ModuleAnalyzer
from sphinx.testing.path import path
from sphinx.util.osutil import relpath


__all__ = [
    'Struct',
    'SphinxTestApp', 'SphinxTestAppWrapperForSkipBuilding',
    'remove_unicode_literals',
]


def assert_re_search(regex: Pattern, text: str, flags: int = 0) -> None:
    if not re.search(regex, text, flags):
        assert False, '%r did not match %r' % (regex, text)


def assert_not_re_search(regex: Pattern, text: str, flags: int = 0) -> None:
    if re.search(regex, text, flags):
        assert False, '%r did match %r' % (regex, text)


def assert_startswith(thing: str, prefix: str) -> None:
    if not thing.startswith(prefix):
        assert False, '%r does not start with %r' % (thing, prefix)


def assert_node(node: nodes.Node, cls: Any = None, xpath: str = "", **kwargs: Any) -> None:
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
            assert isinstance(node, nodes.Element), \
                'The node%s does not have any items' % xpath
            assert len(node) == len(cls), \
                'The node%s has %d child nodes, not %r' % (xpath, len(node), len(cls))
            for i, nodecls in enumerate(cls):
                path = xpath + "[%d]" % i
                assert_node(node[i], nodecls, xpath=path, **kwargs)
        elif isinstance(cls, str):
            assert node == cls, 'The node %r is not %r: %r' % (xpath, cls, node)
        else:
            assert isinstance(node, cls), \
                'The node%s is not subclass of %r: %r' % (xpath, cls, node)

    if kwargs:
        assert isinstance(node, nodes.Element), \
            'The node%s does not have any attributes' % xpath

        for key, value in kwargs.items():
            assert key in node, \
                'The node%s does not have %r attribute: %r' % (xpath, key, node)
            assert node[key] == value, \
                'The node%s[%s] is not %r: %r' % (xpath, key, value, node[key])


def etree_parse(path: str) -> Any:
    with warnings.catch_warnings(record=False):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return ElementTree.parse(path)


class Struct:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)


class SphinxTestApp(application.Sphinx):
    """
    A subclass of :class:`Sphinx` that runs on the test root, with some
    better default values for the initialization parameters.
    """

    def __init__(self, buildername: str = 'html', srcdir: path = None, freshenv: bool = False,
                 confoverrides: Dict = None, status: IO = None, warning: IO = None,
                 tags: List[str] = None, docutilsconf: str = None) -> None:

        if docutilsconf is not None:
            (srcdir / 'docutils.conf').write_text(docutilsconf)

        builddir = srcdir / '_build'
        confdir = srcdir
        outdir = builddir.joinpath(buildername)
        outdir.makedirs(exist_ok=True)
        doctreedir = builddir.joinpath('doctrees')
        doctreedir.makedirs(exist_ok=True)
        if confoverrides is None:
            confoverrides = {}
        warningiserror = False

        self._saved_path = sys.path[:]
        self._saved_directives = directives._directives.copy()  # type: ignore
        self._saved_roles = roles._roles.copy()  # type: ignore

        self._saved_nodeclasses = {v for v in dir(nodes.GenericNodeVisitor)
                                   if v.startswith('visit_')}

        try:
            super().__init__(srcdir, confdir, outdir, doctreedir,
                             buildername, confoverrides, status, warning,
                             freshenv, warningiserror, tags)
        except Exception:
            self.cleanup()
            raise

    def cleanup(self, doctrees: bool = False) -> None:
        ModuleAnalyzer.cache.clear()
        LaTeXBuilder.usepackages = []
        locale.translators.clear()
        sys.path[:] = self._saved_path
        sys.modules.pop('autodoc_fodder', None)
        directives._directives = self._saved_directives  # type: ignore
        roles._roles = self._saved_roles  # type: ignore
        for method in dir(nodes.GenericNodeVisitor):
            if method.startswith('visit_') and \
               method not in self._saved_nodeclasses:
                delattr(nodes.GenericNodeVisitor, 'visit_' + method[6:])
                delattr(nodes.GenericNodeVisitor, 'depart_' + method[6:])

    def __repr__(self) -> str:
        return '<%s buildername=%r>' % (self.__class__.__name__, self.builder.name)


class SphinxTestAppWrapperForSkipBuilding:
    """
    This class is a wrapper for SphinxTestApp to speed up the test by skipping
    `app.build` process if it is already built and there is even one output
    file.
    """

    def __init__(self, app_: SphinxTestApp) -> None:
        self.app = app_

    def __getattr__(self, name: str) -> Any:
        return getattr(self.app, name)

    def build(self, *args: Any, **kwargs: Any) -> None:
        if not self.app.outdir.listdir():  # type: ignore
            # if listdir is empty, do build.
            self.app.build(*args, **kwargs)
            # otherwise, we can use built cache


_unicode_literals_re = re.compile(r'u(".*?")|u(\'.*?\')')


def remove_unicode_literals(s: str) -> str:
    warnings.warn('remove_unicode_literals() is deprecated.',
                  RemovedInSphinx40Warning, stacklevel=2)
    return _unicode_literals_re.sub(lambda x: x.group(1) or x.group(2), s)


def find_files(root: str, suffix: bool = None) -> Generator[str, None, None]:
    for dirpath, dirs, files in os.walk(root, followlinks=True):
        dirpath = path(dirpath)
        for f in [f for f in files if not suffix or f.endswith(suffix)]:  # type: ignore
            fpath = dirpath / f
            yield relpath(fpath, root)


def strip_escseq(text: str) -> str:
    return re.sub('\x1b.*?m', '', text)
