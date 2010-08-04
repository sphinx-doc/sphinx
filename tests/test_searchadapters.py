# -*- coding: utf-8 -*-
"""
    test_searchadapters
    ~~~~~~~~~~~~~~~~~~~

    Test the Web Support Package search adapters.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from StringIO import StringIO

from util import *
from sphinx.websupport import WebSupport


def clear_builddir():
    (test_root / 'websupport').rmtree(True)


def teardown_module():
    (test_root / 'generated').rmtree(True)
    clear_builddir()


def search_adapter_helper(adapter):
    clear_builddir()
    
    settings = {'outdir': os.path.join(test_root, 'websupport'),
                'status': StringIO(),
                'warning': StringIO()}
    settings.update({'srcdir': test_root,
                     'search': adapter})
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
    s.add_document(u'markup', u'title', u'SomeLongRandomWord')
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
    

def test_xapian():
    # Don't run tests if xapian is not installed.
    try:
        import xapian
        search_adapter_helper('xapian')
    except ImportError:
        sys.stderr.write('info: not running xapian tests, ' \
                         'xapian doesn\'t seem to be installed')


def test_whoosh():
    # Don't run tests if whoosh is not installed.
    try:
        import whoosh
        search_adapter_helper('whoosh')
    except ImportError:
        sys.stderr.write('info: not running whoosh tests, ' \
                         'whoosh doesn\'t seem to be installed')

