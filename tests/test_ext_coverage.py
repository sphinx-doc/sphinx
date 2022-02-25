"""
    test_coverage
    ~~~~~~~~~~~~~

    Test the coverage builder.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pickle

import pytest


@pytest.mark.sphinx('coverage')
def test_build(app, status, warning):
    app.builder.build_all()

    py_undoc = (app.outdir / 'python.txt').read_text()
    assert py_undoc.startswith('Undocumented Python objects\n'
                               '===========================\n')
    assert 'autodoc_target\n--------------\n' in py_undoc
    assert ' * Class -- missing methods:\n' in py_undoc
    assert ' * raises\n' in py_undoc
    assert ' * function\n' not in py_undoc  # these two are documented
    assert ' * Class\n' not in py_undoc     # in autodoc.txt

    assert ' * mod -- No module named mod'  # in the "failed import" section

    assert "undocumented  py" not in status.getvalue()

    c_undoc = (app.outdir / 'c.txt').read_text()
    assert c_undoc.startswith('Undocumented C API elements\n'
                              '===========================\n')
    assert 'api.h' in c_undoc
    assert ' * Py_SphinxTest' in c_undoc

    undoc_py, undoc_c = pickle.loads((app.outdir / 'undoc.pickle').read_bytes())
    assert len(undoc_c) == 1
    # the key is the full path to the header file, which isn't testable
    assert list(undoc_c.values())[0] == {('function', 'Py_SphinxTest')}

    assert 'autodoc_target' in undoc_py
    assert 'funcs' in undoc_py['autodoc_target']
    assert 'raises' in undoc_py['autodoc_target']['funcs']
    assert 'classes' in undoc_py['autodoc_target']
    assert 'Class' in undoc_py['autodoc_target']['classes']
    assert 'undocmeth' in undoc_py['autodoc_target']['classes']['Class']

    assert "undocumented  c" not in status.getvalue()


@pytest.mark.sphinx('coverage', testroot='ext-coverage')
def test_coverage_ignore_pyobjects(app, status, warning):
    app.builder.build_all()
    actual = (app.outdir / 'python.txt').read_text()
    expected = '''Undocumented Python objects
===========================
coverage_not_ignored
--------------------
Classes:
 * Documented -- missing methods:

   - not_ignored1
   - not_ignored2
 * NotIgnored

'''
    assert actual == expected


@pytest.mark.sphinx('coverage', confoverrides={'coverage_show_missing_items': True})
def test_show_missing_items(app, status, warning):
    app.builder.build_all()

    assert "undocumented" in status.getvalue()

    assert "py  function  raises" in status.getvalue()
    assert "py  class     Base" in status.getvalue()
    assert "py  method    Class.roger" in status.getvalue()

    assert "c   api       Py_SphinxTest [ function]" in status.getvalue()


@pytest.mark.sphinx('coverage', confoverrides={'coverage_show_missing_items': True})
def test_show_missing_items_quiet(app, status, warning):
    app.quiet = True
    app.builder.build_all()

    assert "undocumented python function: autodoc_target :: raises" in warning.getvalue()
    assert "undocumented python class: autodoc_target :: Base" in warning.getvalue()
    assert "undocumented python method: autodoc_target :: Class :: roger" in warning.getvalue()

    assert "undocumented c api: Py_SphinxTest [function]" in warning.getvalue()
