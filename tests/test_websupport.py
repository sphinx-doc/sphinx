# -*- coding: utf-8 -*-
"""
    test_websupport
    ~~~~~~~~~~~~~~~

    Test the Web Support Package

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os, sys
from StringIO import StringIO

from sphinx.websupport import WebSupport
from sphinx.websupport.errors import *
from sphinx.websupport.comments.sqlalchemystorage import Session
from sphinx.websupport.comments.db import Node

try:
    from functools import wraps
except ImportError:
    # functools is new in 2.4
    wraps = lambda f: (lambda w: w)

from util import *


default_settings = {'outdir': os.path.join(test_root, 'websupport'),
                    'status': StringIO(),
                    'warning': StringIO()}


def clear_builddir():
    (test_root / 'websupport').rmtree(True)


def teardown_module():
    (test_root / 'generated').rmtree(True)
    clear_builddir()


def with_support(*args, **kwargs):
    """Make a WebSupport object and pass it the test."""
    settings = default_settings.copy()
    settings.update(kwargs)

    def generator(func):
        @wraps(func)
        def new_func(*args2, **kwargs2):
            support = WebSupport(**settings)
            func(support, *args2, **kwargs2)
        return new_func
    return generator


@with_support()
def test_no_srcdir(support):
    """Make sure the correct exception is raised if srcdir is not given."""
    raises(SrcdirNotSpecifiedError, support.build)


@with_support(srcdir=test_root)
def test_build(support):
    support.build()


@with_support()
def test_get_document(support):
    raises(DocumentNotFoundError, support.get_document, 'nonexisting')
    
    contents = support.get_document('contents')
    assert contents['title'] and contents['body'] \
        and contents['sidebar'] and contents['relbar']


def search_adapter_helper(adapter):
    clear_builddir()
    
    settings = default_settings.copy()
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


@with_support()
def test_comments(support):
    session = Session()
    nodes = session.query(Node).all()
    first_node = nodes[0]
    second_node = nodes[1]

    # Create a displayed comment and a non displayed comment.
    comment = support.add_comment('First test comment', 
                                  node_id=str(first_node.id))
    support.add_comment('Hidden comment', node_id=str(first_node.id), 
                        displayed=False)
    # Add a displayed and not displayed child to the displayed comment.
    support.add_comment('Child test comment', parent_id=str(comment['id']))
    support.add_comment('Hidden child test comment', 
                        parent_id=str(comment['id']), displayed=False)
    # Add a comment to another node to make sure it isn't returned later.
    support.add_comment('Second test comment', 
                        node_id=str(second_node.id))
    
    # Access the comments as a moderator.
    data = support.get_comments(str(first_node.id), moderator=True)
    comments = data['comments']
    children = comments[0]['children']
    assert len(comments) == 2
    assert comments[1]['text'] == 'Hidden comment'
    assert len(children) == 2
    assert children[1]['text'] == 'Hidden child test comment'

    # Access the comments without being a moderator.
    data = support.get_comments(str(first_node.id))
    comments = data['comments']
    children = comments[0]['children']
    assert len(comments) == 1
    assert comments[0]['text'] == 'First test comment'
    assert len(children) == 1
    assert children[0]['text'] == 'Child test comment'

    def check_rating(val):
        data = support.get_comments(str(first_node.id))
        comment = data['comments'][0]
        assert comment['rating'] == val, '%s != %s' % (comment['rating'], val)
        
    support.process_vote(comment['id'], 'user_one', '1')
    support.process_vote(comment['id'], 'user_two', '1')
    support.process_vote(comment['id'], 'user_three', '1')
    check_rating(3)
    support.process_vote(comment['id'], 'user_one', '-1')
    check_rating(1)
    support.process_vote(comment['id'], 'user_one', '0')
    check_rating(2)

    # Make sure a vote with value > 1 or < -1 can't be cast.
    raises(ValueError, support.process_vote, comment['id'], 'user_one', '2')
    raises(ValueError, support.process_vote, comment['id'], 'user_one', '-2')

    # Make sure past voting data is associated with comments when they are
    # fetched.
    data = support.get_comments(str(first_node.id), username='user_two')
    comment = data['comments'][0]
    assert comment['vote'] == 1, '%s != 1' % comment['vote']
