"""
    test_metadata
    ~~~~~~~~~~~~~

    Test our handling of metadata in files with bibliographic metadata.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# adapted from an example of bibliographic metadata at
# https://docutils.sourceforge.io/docs/user/rst/demo.txt

import pytest


@pytest.mark.sphinx('dummy', testroot='metadata')
def test_docinfo(app, status, warning):
    """
    Inspect the 'docinfo' metadata stored in the first node of the document.
    Note this doesn't give us access to data stored in subsequence blocks
    that might be considered document metadata, such as 'abstract' or
    'dedication' blocks, or the 'meta' role. Doing otherwise is probably more
    messing with the internals of sphinx than this rare use case merits.
    """
    app.build()
    expecteddocinfo = {
        'author': 'David Goodger',
        'authors': ['Me', 'Myself', 'I'],
        'address': '123 Example Street\nExample, EX  Canada\nA1B 2C3',
        'field name': 'This is a generic bibliographic field.',
        'field name 2': ('Generic bibliographic fields may contain multiple '
                         'body elements.\n\nLike this.'),
        'status': 'This is a “work in progress”',
        'version': '1',
        'copyright': ('This document has been placed in the public domain. '
                      'You\nmay do with it as you wish. You may copy, modify,'
                      '\nredistribute, reattribute, sell, buy, rent, lease,\n'
                      'destroy, or improve it, quote it at length, excerpt,\n'
                      'incorporate, collate, fold, staple, or mutilate it, or '
                      'do\nanything else to it that your or anyone else’s '
                      'heart\ndesires.'),
        'contact': 'goodger@python.org',
        'date': '2006-05-21',
        'organization': 'humankind',
        'revision': '4564',
        'tocdepth': 1,
        'orphan': '',
        'nocomments': '',
    }
    assert app.env.metadata['index'] == expecteddocinfo
