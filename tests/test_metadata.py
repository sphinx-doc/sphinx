# -*- coding: utf-8 -*-
"""
    test_metadata
    ~~~~~~~~~~~~~

    Test our handling of metadata in files with bibliographic metadata.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# adapted from an example of bibliographic metadata at
# http://docutils.sourceforge.net/docs/user/rst/demo.txt

from util import with_app

from nose.tools import assert_equal


@with_app('pseudoxml')
def test_docinfo(app, status, warning):
    """
    Inspect the 'docinfo' metadata stored in the first node of the document.
    Note this doesn't give us access to data stored in subsequence blocks
    that might be considered document metadata, such as 'abstract' or
    'dedication' blocks, or the 'meta' role. Doing otherwise is probably more
    messing with the internals of sphinx than this rare use case merits.
    """
    app.builder.build(['metadata'])
    env = app.env
    exampledocinfo = env.metadata['metadata']
    expecteddocinfo = {
        'author': u'David Goodger',
        'authors': [u'Me', u'Myself', u'I'],
        'address': u'123 Example Street\nExample, EX  Canada\nA1B 2C3',
        'field name': u'This is a generic bibliographic field.',
        'field name 2': (u'Generic bibliographic fields may contain multiple '
                         u'body elements.\n\nLike this.'),
        'status': u'This is a "work in progress"',
        'version': u'1',
        'copyright': (u'This document has been placed in the public domain. '
                      u'You\nmay do with it as you wish. You may copy, modify,'
                      u'\nredistribute, reattribute, sell, buy, rent, lease,\n'
                      u'destroy, or improve it, quote it at length, excerpt,\n'
                      u'incorporate, collate, fold, staple, or mutilate it, or '
                      u'do\nanything else to it that your or anyone else\'s '
                      u'heart\ndesires.'),
        'contact': u'goodger@python.org',
        'date': u'2006-05-21',
        'organization': u'humankind',
        'revision': u'4564',
        'tocdepth': 1,
        'orphan': u'',
        'nocomments': u'',
    }
    # I like this way of comparing dicts - easier to see the error.
    for key in exampledocinfo:
        yield assert_equal, exampledocinfo.get(key), expecteddocinfo.get(key)
    # but then we still have to check for missing keys
    yield assert_equal, set(expecteddocinfo.keys()), set(exampledocinfo.keys())
