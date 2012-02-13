# -*- coding: utf-8 -*-
"""
    test_websupport
    ~~~~~~~~~~~~~~~

    Test the Web Support Package

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from StringIO import StringIO

try:
    from functools import wraps
except ImportError:
    # functools is new in 2.5
    wraps = lambda f: (lambda w: w)

from sphinx.websupport import WebSupport
from sphinx.websupport.errors import *
from sphinx.websupport.storage import StorageBackend
from sphinx.websupport.storage.differ import CombinedHtmlDiff
try:
    from sphinx.websupport.storage.sqlalchemystorage import Session, \
         Comment, CommentVote
    from sphinx.websupport.storage.sqlalchemy_db import Node
    sqlalchemy_missing = False
except ImportError:
    sqlalchemy_missing = True

from util import *


default_settings = {'builddir': os.path.join(test_root, 'websupport'),
                    'status': StringIO(),
                    'warning': StringIO()}

def teardown_module():
    (test_root / 'generated').rmtree(True)
    (test_root / 'websupport').rmtree(True)


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


class NullStorage(StorageBackend):
    pass


@with_support(storage=NullStorage())
def test_no_srcdir(support):
    """Make sure the correct exception is raised if srcdir is not given."""
    raises(RuntimeError, support.build)


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support(srcdir=test_root)
def test_build(support):
    support.build()


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support()
def test_get_document(support):
    raises(DocumentNotFoundError, support.get_document, 'nonexisting')

    contents = support.get_document('contents')
    assert contents['title'] and contents['body'] \
        and contents['sidebar'] and contents['relbar']


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support()
def test_comments(support):
    session = Session()
    nodes = session.query(Node).all()
    first_node = nodes[0]
    second_node = nodes[1]

    # Create a displayed comment and a non displayed comment.
    comment = support.add_comment('First test comment',
                                  node_id=first_node.id,
                                  username='user_one')
    hidden_comment = support.add_comment('Hidden comment',
                                         node_id=first_node.id,
                                         displayed=False)
    # Make sure that comments can't be added to a comment where
    # displayed == False, since it could break the algorithm that
    # converts a nodes comments to a tree.
    raises(CommentNotAllowedError, support.add_comment, 'Not allowed',
           parent_id=str(hidden_comment['id']))
    # Add a displayed and not displayed child to the displayed comment.
    support.add_comment('Child test comment', parent_id=str(comment['id']),
                        username='user_one')
    support.add_comment('Hidden child test comment',
                        parent_id=str(comment['id']), displayed=False)
    # Add a comment to another node to make sure it isn't returned later.
    support.add_comment('Second test comment',
                        node_id=second_node.id,
                        username='user_two')

    # Access the comments as a moderator.
    data = support.get_data(first_node.id, moderator=True)
    comments = data['comments']
    children = comments[0]['children']
    assert len(comments) == 2
    assert comments[1]['text'] == '<p>Hidden comment</p>\n'
    assert len(children) == 2
    assert children[1]['text'] == '<p>Hidden child test comment</p>\n'

    # Access the comments without being a moderator.
    data = support.get_data(first_node.id)
    comments = data['comments']
    children = comments[0]['children']
    assert len(comments) == 1
    assert comments[0]['text'] == '<p>First test comment</p>\n'
    assert len(children) == 1
    assert children[0]['text'] == '<p>Child test comment</p>\n'


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support()
def test_voting(support):
    session = Session()
    nodes = session.query(Node).all()
    node = nodes[0]

    comment = support.get_data(node.id)['comments'][0]

    def check_rating(val):
        data = support.get_data(node.id)
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
    data = support.get_data(str(node.id), username='user_two')
    comment = data['comments'][0]
    assert comment['vote'] == 1, '%s != 1' % comment['vote']


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support()
def test_proposals(support):
    session = Session()
    node = session.query(Node).first()

    data = support.get_data(node.id)

    source = data['source']
    proposal = source[:5] + source[10:15] + 'asdf' + source[15:]

    comment = support.add_comment('Proposal comment',
                                  node_id=node.id,
                                  proposal=proposal)


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support()
def test_user_delete_comments(support):
    def get_comment():
        session = Session()
        node = session.query(Node).first()
        session.close()
        return support.get_data(node.id)['comments'][0]

    comment = get_comment()
    assert comment['username'] == 'user_one'
    # Make sure other normal users can't delete someone elses comments.
    raises(UserNotAuthorizedError, support.delete_comment,
           comment['id'], username='user_two')
    # Now delete the comment using the correct username.
    support.delete_comment(comment['id'], username='user_one')
    comment = get_comment()
    assert comment['username'] == '[deleted]'
    assert comment['text'] == '[deleted]'


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support()
def test_moderator_delete_comments(support):
    def get_comment():
        session = Session()
        node = session.query(Node).first()
        session.close()
        return support.get_data(node.id, moderator=True)['comments'][1]

    comment = get_comment()
    support.delete_comment(comment['id'], username='user_two',
                           moderator=True)
    raises(IndexError, get_comment)


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support()
def test_update_username(support):
    support.update_username('user_two', 'new_user_two')
    session = Session()
    comments = session.query(Comment).\
        filter(Comment.username == 'user_two').all()
    assert len(comments) == 0
    votes = session.query(CommentVote).\
        filter(CommentVote.username == 'user_two').all()
    assert len(votes) == 0
    comments = session.query(Comment).\
        filter(Comment.username == 'new_user_two').all()
    assert len(comments) == 1
    votes = session.query(CommentVote).\
        filter(CommentVote.username == 'new_user_two').all()
    assert len(votes) == 0


called = False
def moderation_callback(comment):
    global called
    called = True


@skip_if(sqlalchemy_missing, 'needs sqlalchemy')
@with_support(moderation_callback=moderation_callback)
def test_moderation(support):
    session = Session()
    nodes = session.query(Node).all()
    node = nodes[7]
    session.close()
    accepted = support.add_comment('Accepted Comment', node_id=node.id,
                                   displayed=False)
    deleted  = support.add_comment('Comment to delete', node_id=node.id,
                                   displayed=False)
    # Make sure the moderation_callback is called.
    assert called == True
    # Make sure the user must be a moderator.
    raises(UserNotAuthorizedError, support.accept_comment, accepted['id'])
    raises(UserNotAuthorizedError, support.delete_comment, deleted['id'])
    support.accept_comment(accepted['id'], moderator=True)
    support.delete_comment(deleted['id'], moderator=True)
    comments = support.get_data(node.id)['comments']
    assert len(comments) == 1
    comments = support.get_data(node.id, moderator=True)['comments']
    assert len(comments) == 1


def test_differ():
    source = 'Lorem ipsum dolor sit amet,\nconsectetur adipisicing elit,\n' \
        'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    prop = 'Lorem dolor sit amet,\nconsectetur nihil adipisicing elit,\n' \
        'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    differ = CombinedHtmlDiff(source, prop)
    differ.make_html()
