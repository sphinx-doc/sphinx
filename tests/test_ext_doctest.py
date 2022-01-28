"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
from collections import Counter

import pytest
from docutils import nodes
from packaging.specifiers import InvalidSpecifier
from packaging.version import InvalidVersion

from sphinx.ext.doctest import is_allowed_version

cleanup_called = 0


@pytest.mark.sphinx('doctest', testroot='ext-doctest')
def test_build(app, status, warning):
    global cleanup_called
    cleanup_called = 0
    app.builder.build_all()
    if app.statuscode != 0:
        assert False, 'failures in doctests:' + status.getvalue()
    # in doctest.txt, there are two named groups and the default group,
    # so the cleanup function must be called three times
    assert cleanup_called == 3, 'testcleanup did not get executed enough times'


@pytest.mark.sphinx('dummy', testroot='ext-doctest')
def test_highlight_language_default(app, status, warning):
    app.build()
    doctree = app.env.get_doctree('doctest')
    for node in doctree.findall(nodes.literal_block):
        assert node['language'] in ('python3', 'pycon3', 'none')


@pytest.mark.sphinx('dummy', testroot='ext-doctest',
                    confoverrides={'highlight_language': 'python'})
def test_highlight_language_python2(app, status, warning):
    app.build()
    doctree = app.env.get_doctree('doctest')
    for node in doctree.findall(nodes.literal_block):
        assert node['language'] in ('python', 'pycon', 'none')


def test_is_allowed_version():
    assert is_allowed_version('<3.4', '3.3') is True
    assert is_allowed_version('<3.4', '3.3') is True
    assert is_allowed_version('<3.2', '3.3') is False
    assert is_allowed_version('<=3.4',  '3.3') is True
    assert is_allowed_version('<=3.2',  '3.3') is False
    assert is_allowed_version('==3.3',  '3.3') is True
    assert is_allowed_version('==3.4',  '3.3') is False
    assert is_allowed_version('>=3.2',  '3.3') is True
    assert is_allowed_version('>=3.4',  '3.3') is False
    assert is_allowed_version('>3.2', '3.3') is True
    assert is_allowed_version('>3.4', '3.3') is False
    assert is_allowed_version('~=3.4', '3.4.5') is True
    assert is_allowed_version('~=3.4', '3.5.0') is True

    # invalid spec
    with pytest.raises(InvalidSpecifier):
        is_allowed_version('&3.4', '3.5')

    # invalid version
    with pytest.raises(InvalidVersion):
        is_allowed_version('>3.4', 'Sphinx')


def cleanup_call():
    global cleanup_called
    cleanup_called += 1


recorded_calls = Counter()


@pytest.mark.sphinx('doctest', testroot='ext-doctest-skipif')
def test_skipif(app, status, warning):
    """Tests for the :skipif: option

    The tests are separated into a different test root directory since the
    ``app`` object only evaluates options once in its lifetime. If these tests
    were combined with the other doctest tests, the ``:skipif:`` evaluations
    would be recorded only on the first ``app.builder.build_all()`` run, i.e.
    in ``test_build`` above, and the assertion below would fail.

    """
    global recorded_calls
    recorded_calls = Counter()
    app.builder.build_all()
    if app.statuscode != 0:
        assert False, 'failures in doctests:' + status.getvalue()
    # The `:skipif:` expressions are always run.
    # Actual tests and setup/cleanup code is only run if the `:skipif:`
    # expression evaluates to a False value.
    # Global setup/cleanup are run before/after evaluating the `:skipif:`
    # option in each directive - thus 11 additional invocations for each on top
    # of the ones made for the whole test file.
    assert recorded_calls == {('doctest_global_setup', 'body', True): 13,
                              ('testsetup', ':skipif:', True): 1,
                              ('testsetup', ':skipif:', False): 1,
                              ('testsetup', 'body', False): 1,
                              ('doctest', ':skipif:', True): 1,
                              ('doctest', ':skipif:', False): 1,
                              ('doctest', 'body', False): 1,
                              ('testcode', ':skipif:', True): 1,
                              ('testcode', ':skipif:', False): 1,
                              ('testcode', 'body', False): 1,
                              ('testoutput-1', ':skipif:', True): 1,
                              ('testoutput-2', ':skipif:', True): 1,
                              ('testoutput-2', ':skipif:', False): 1,
                              ('testcleanup', ':skipif:', True): 1,
                              ('testcleanup', ':skipif:', False): 1,
                              ('testcleanup', 'body', False): 1,
                              ('doctest_global_cleanup', 'body', True): 13}


def record(directive, part, should_skip):
    global recorded_calls
    recorded_calls[(directive, part, should_skip)] += 1
    return 'Recorded {} {} {}'.format(directive, part, should_skip)


@pytest.mark.sphinx('doctest', testroot='ext-doctest-with-autodoc')
def test_reporting_with_autodoc(app, status, warning, capfd):
    # Patch builder to get a copy of the output
    written = []
    app.builder._warn_out = written.append
    app.builder.build_all()
    lines = '\n'.join(written).replace(os.sep, '/').split('\n')
    failures = [l for l in lines if l.startswith('File')]
    expected = [
        'File "dir/inner.rst", line 1, in default',
        'File "dir/bar.py", line ?, in default',
        'File "foo.py", line ?, in default',
        'File "index.rst", line 4, in default',
    ]
    for location in expected:
        assert location in failures
