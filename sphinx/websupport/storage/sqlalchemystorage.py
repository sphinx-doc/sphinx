# -*- coding: utf-8 -*-
"""
    sphinx.websupport.storage.sqlalchemystorage
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    An SQLAlchemy storage backend.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from datetime import datetime

from sphinx.websupport.errors import *
from sphinx.websupport.storage import StorageBackend
from sphinx.websupport.storage.db import Base, Node, Comment, CommentVote,\
                                          Session
from sphinx.websupport.storage.differ import CombinedHtmlDiff

class SQLAlchemyStorage(StorageBackend):
    def __init__(self, engine):
        self.engine = engine
        Base.metadata.bind = engine
        Base.metadata.create_all()
        Session.configure(bind=engine)

    def pre_build(self):
        self.build_session = Session()

    def add_node(self, document, line, source, treeloc):
        node = Node(document, line, source, treeloc)
        self.build_session.add(node)
        self.build_session.flush()
        return node.id

    def post_build(self):
        self.build_session.commit()
        self.build_session.close()

    def add_comment(self, text, displayed, username, rating, time,
                    proposal, node_id, parent_id, moderator):
        session = Session()
        
        if node_id and proposal:
            node = session.query(Node).filter(Node.id == node_id).one()
            differ = CombinedHtmlDiff()
            proposal_diff = differ.make_html(node.source, proposal)
        elif parent_id:
            parent = session.query(Comment.displayed).\
                filter(Comment.id == parent_id).one()
            if not parent.displayed:
                raise CommentNotAllowedError(
                    "Can't add child to a parent that is not displayed")
            proposal_diff = None
        else:
            proposal_diff = None

        comment = Comment(text, displayed, username, rating, 
                          time or datetime.now(), proposal, proposal_diff)
        session.add(comment)
        session.flush()
        comment.set_path(node_id, parent_id)
        session.commit()
        comment = comment.serializable()
        session.close()
        return comment

    def delete_comment(self, comment_id, username, moderator):
        session = Session()
        comment = session.query(Comment).\
            filter(Comment.id == comment_id).one()
        if moderator or comment.username == username:
            comment.username = '[deleted]'
            comment.text = '[deleted]'
            session.commit()
            session.close()
        else:
            session.close()
            raise UserNotAuthorizedError()

    def get_data(self, node_id, username, moderator):
        session = Session()
        node = session.query(Node).filter(Node.id == node_id).one()
        session.close()
        comments = node.nested_comments(username, moderator)
        return {'source': node.source,
                'comments': comments}

    def process_vote(self, comment_id, username, value):
        session = Session()
        vote = session.query(CommentVote).filter(
            CommentVote.comment_id == comment_id).filter(
            CommentVote.username == username).first()

        comment = session.query(Comment).filter(
            Comment.id == comment_id).first()

        if vote is None:
            vote = CommentVote(comment_id, username, value)
            comment.rating += value
        else:
            comment.rating += value - vote.value
            vote.value = value
        session.add(vote)
        session.commit()
        session.close()

    def update_username(self, old_username, new_username):
        session = Session()
        session.query(Comment).filter(Comment.username == old_username).\
            update({Comment.username: new_username})
        session.query(CommentVote).\
            filter(CommentVote.username == old_username).\
            update({CommentVote.username: new_username})
        session.commit()
        session.close()

    def accept_comment(self, comment_id):
        session = Session()
        comment = session.query(Comment).\
            filter(Comment.id == comment_id).one()
        comment.displayed = True
        session.commit()
        session.close()

    def reject_comment(self, comment_id):
        session = Session()
        comment = session.query(Comment).\
            filter(Comment.id == comment_id).one()
        session.delete(comment)
        session.commit()
        session.close()
