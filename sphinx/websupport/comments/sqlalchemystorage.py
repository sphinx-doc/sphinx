# -*- coding: utf-8 -*-
"""
    sphinx.websupport.comments.sqlalchemystorage
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A SQLAlchemy storage backend.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from datetime import datetime

from sqlalchemy.orm import aliased
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
                    proposal, node_id, parent_id, moderator):
        session = Session()
        
        if node_id and proposal:
            node = session.query(Node).filter(Node.id == node_id).one()
            differ = CombinedHtmlDiff()
            proposal_diff = differ.make_html(node.source, proposal)
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

    def get_comments(self, node_id, username, moderator):
        session = Session()
        node = session.query(Node).filter(Node.id == node_id).one()
        session.close()
        comments = self._serializable_list(node_id, username, moderator)
        return {'source': node.source,
                'comments': comments}

    def _serializable_list(self, node_id, username, moderator):
        session = Session()

        if username:
            # If a username is provided, create a subquery to retrieve all
            # votes by this user. We will outerjoin with the comment query
            # with this subquery so we have a user's voting information.
            sq = session.query(CommentVote).\
                filter(CommentVote.username == username).subquery()
            cvalias = aliased(CommentVote, sq)
            q = session.query(Comment, cvalias.value).outerjoin(cvalias)
        else:
            q = session.query(Comment)

        # Filter out all comments not descending from this node.
        q = q.filter(Comment.path.like(node_id + '.%'))
        # Filter out non-displayed comments if this isn't a moderator.
        if not moderator:
            q = q.filter(Comment.displayed == True)
        # Retrieve all results. Results must be ordered by Comment.path
        # so that we can easily transform them from a flat list to a tree.
        results = q.order_by(Comment.path).all()
        session.close()

        # We now need to convert the flat list of results to a nested
        # lists to form the comment tree. Results will by ordered by
        # the materialized path.
        comments = []
        list_stack = [comments]
        for r in results:
            comment, vote = r if username else (r, 0)

            inheritance_chain = comment.path.split('.')[1:]
            
            if len(inheritance_chain) == len(list_stack) + 1:
                parent = list_stack[-1][-1]
                list_stack.append(parent['children'])
            elif len(inheritance_chain) < len(list_stack):
                while len(inheritance_chain) < len(list_stack):
                    list_stack.pop()

            list_stack[-1].append(comment.serializable(vote=vote))
        
        return comments

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
