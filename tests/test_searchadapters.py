# -*- coding: utf-8 -*-
"""
    test_searchadapters
    ~~~~~~~~~~~~~~~~~~~

    Test the Web Support Package search adapters.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import StringIO

from sphinx.websupport import WebSupport

from test_websupport import sqlalchemy_missing
from util import rootdir, tempdir, skip_if, skip_unless_importable


def teardown_module():
    (tempdir / 'websupport').rmtree(True)


def search_adapter_helper(adapter):
    settings = {'srcdir': rootdir / 'roots' / 'test-searchadapters',
                'builddir': tempdir / 'websupport',
                'status': StringIO(),
                'warning': StringIO(),
                'search': adapter}
    support = WebSupport(**settings)
    support.build()

    s = support.search

    # Test the adapters query method. A search for "Epigraph" should return
    # one result.
    results = s.query(u'Epigraph')
    assert len(results) == 1, \
        '%s search adapter returned %s search result(s), should have been 1'\
        % (adapter, len(results))

    # Make sure documents are properly updated by the search adapter.
    s.init_indexing(changed=['markup'])
    s.add_document(u'markup', u'filename', u'title', u'SomeLongRandomWord')
    s.finish_indexing()
    # Now a search for "Epigraph" should return zero results.
    results = s.query(u'Epigraph')
    assert len(results) == 0, \
        '%s search adapter returned %s search result(s), should have been 0'\
        % (adapter, len(results))
    # A search for "SomeLongRandomWord" should return one result.
    results = s.query(u'SomeLongRandomWord')
    assert len(results) == 1, \
        '%s search adapter returned %s search result(s), should have been 1'\
        % (adapter, len(results))
    # Make sure it works through the WebSupport API
    support.get_search_results(u'SomeLongRandomWord')


@skip_unless_importable('xapian', 'needs xapian bindings installed')
@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
def test_xapian():
    search_adapter_helper('xapian')


@skip_unless_importable('whoosh', 'needs whoosh package installed')
@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
def test_whoosh():
    search_adapter_helper('whoosh')
