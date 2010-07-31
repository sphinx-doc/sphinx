# -*- coding: utf-8 -*-
"""
    sphinx.websupport.comments.sqlalchemystorage
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A SQLAlchemy storage backend.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from datetime import datetime

from sphinx.websupport.comments import StorageBackend
from sphinx.websupport.comments.db import Base, Node, Comment, CommentVote,\
                                          Session
from sphinx.websupport.comments.differ import CombinedHtmlDiff

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
                    proposal, node, parent):
        session = Session()
        
        if node:
            node = session.query(Node).filter(Node.id == node).first()
            parent = None
        else:
            node = None
            parent = session.query(Comment).filter(
                Comment.id == parent).first()
        if node and proposal:
            differ = CombinedHtmlDiff()
            proposal_diff = differ.make_html(node.source, proposal)
        else:
            proposal_diff = None

        comment = Comment(text, displayed, username, rating, 
                          time or datetime.now(), proposal, proposal_diff, 
                          node, parent)
        session.add(comment)
        session.commit()
        comment = comment.serializable()
        session.close()
        return comment

    def get_comments(self, node_id, user_id):
        session = Session()
        node = session.query(Node).filter(Node.id == node_id).first()
        data = {'source': node.source,
                'comments': [comment.serializable(user_id)
                             for comment in node.comments]}
        session.close()
        return data

    def process_vote(self, comment_id, user_id, value):
        session = Session()
        vote = session.query(CommentVote).filter(
            CommentVote.comment_id == comment_id).filter(
            CommentVote.user_id == user_id).first()

        comment = session.query(Comment).filter(
            Comment.id == comment_id).first()

        if vote is None:
            vote = CommentVote(comment_id, user_id, value)
            comment.rating += value
        else:
            comment.rating += value - vote.value
            vote.value = value
        session.add(vote)
        session.commit()
        session.close()
