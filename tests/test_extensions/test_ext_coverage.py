"""Test the coverage builder."""

from __future__ import annotations

import pickle
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('coverage', testroot='root')
def test_build(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    py_undoc = (app.outdir / 'python.txt').read_text(encoding='utf8')
    assert py_undoc.startswith(
        'Undocumented Python objects\n===========================\n',
    )
    assert 'autodoc_target\n--------------\n' in py_undoc
    assert ' * Class -- missing methods:\n' in py_undoc
    assert ' * raises\n' in py_undoc
    # these two are documented in autodoc.txt
    assert ' * function\n' not in py_undoc
    assert ' * Class\n' not in py_undoc

    # in the "failed import" section
    assert " * mod -- No module named 'mod'" in py_undoc

    assert 'undocumented  py' not in app.status.getvalue()

    c_undoc = (app.outdir / 'c.txt').read_text(encoding='utf8')
    assert c_undoc.startswith(
        'Undocumented C API elements\n===========================\n',
    )
    assert 'api.h' in c_undoc
    assert ' * Py_SphinxTest' in c_undoc

    undoc_py, undoc_c, _py_undocumented, _py_documented = pickle.loads(
        (app.outdir / 'undoc.pickle').read_bytes()
    )
    assert len(undoc_c) == 1
    # the key is the full path to the header file, which isn't testable
    assert next(iter(undoc_c.values())) == {('function', 'Py_SphinxTest')}

    assert 'autodoc_target' in undoc_py
    assert 'funcs' in undoc_py['autodoc_target']
    assert 'raises' in undoc_py['autodoc_target']['funcs']
    assert 'classes' in undoc_py['autodoc_target']
    assert 'Class' in undoc_py['autodoc_target']['classes']
    assert 'undocmeth' in undoc_py['autodoc_target']['classes']['Class']

    assert 'undocumented  c' not in app.status.getvalue()


@pytest.mark.sphinx('coverage', testroot='ext-coverage')
def test_coverage_ignore_pyobjects(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    actual = (app.outdir / 'python.txt').read_text(encoding='utf8')
    expected = """\
Undocumented Python objects
===========================

Statistics
----------

+---------------------------+----------+--------------+
| Module                    | Coverage | Undocumented |
+===========================+==========+==============+
| grog                      | 100.00%  | 0            |
+---------------------------+----------+--------------+
| grog.coverage_missing     | 100.00%  | 0            |
+---------------------------+----------+--------------+
| grog.coverage_not_ignored | 0.00%    | 2            |
+---------------------------+----------+--------------+
| TOTAL                     | 0.00%    | 2            |
+---------------------------+----------+--------------+

grog.coverage_missing
---------------------

Classes:
 * Missing

grog.coverage_not_ignored
-------------------------

Classes:
 * Documented -- missing methods:

   - not_ignored1
   - not_ignored2
 * NotIgnored

"""
    assert actual == expected


@pytest.mark.sphinx(
    'coverage', testroot='root', confoverrides={'coverage_show_missing_items': True}
)
def test_show_missing_items(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    assert 'undocumented' in app.status.getvalue()

    assert 'py  function  raises' in app.status.getvalue()
    assert 'py  class     Base' in app.status.getvalue()
    assert 'py  method    Class.roger' in app.status.getvalue()

    assert 'c   api       Py_SphinxTest [ function]' in app.status.getvalue()


@pytest.mark.sphinx(
    'coverage', testroot='root', confoverrides={'coverage_show_missing_items': True}
)
def test_show_missing_items_quiet(app: SphinxTestApp) -> None:
    app.config._verbosity = -1  # mimics status=None / app.quiet = True
    app.build(force_all=True)

    assert (
        'undocumented python function: autodoc_target :: raises'
    ) in app.warning.getvalue()
    assert 'undocumented python class: autodoc_target :: Base' in app.warning.getvalue()
    assert (
        'undocumented python method: autodoc_target :: Class :: roger'
    ) in app.warning.getvalue()

    assert 'undocumented c api: Py_SphinxTest [function]' in app.warning.getvalue()
