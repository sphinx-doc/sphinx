# -*- coding: utf-8 -*-
"""
    sphinx.websupport.storage.db
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SQLAlchemy table and mapper definitions used by the
    :class:`sphinx.websupport.comments.SQLAlchemyStorage`.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, Text, String, Boolean, ForeignKey,\
                       DateTime
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, sessionmaker, aliased

Base = declarative_base()

Session = sessionmaker()

db_prefix = 'sphinx_'

class Node(Base):
    """Data about a Node in a doctree."""
    __tablename__ = db_prefix + 'nodes'

    id = Column(Integer, primary_key=True)
    document = Column(String(256), nullable=False)
    line = Column(Integer)
    source = Column(Text, nullable=False)

    def nested_comments(self, username, moderator):
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
        q = q.filter(Comment.path.like(str(self.id) + '.%'))
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
        return self._nest_comments(results, username)

    def _nest_comments(self, results, username):
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

    def __init__(self, document, line, source, treeloc):
        self.document = document
        self.line = line
        self.source = source
        self.treeloc = treeloc

class Comment(Base):
    __tablename__ = db_prefix + 'comments'

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    text = Column(Text, nullable=False)
    displayed = Column(Boolean, index=True, default=False)
    username = Column(String(64))
    proposal = Column(Text)
    proposal_diff = Column(Text)
    path = Column(String(256), index=True)

    def __init__(self, text, displayed, username, rating, time, 
                 proposal, proposal_diff):
        self.text = text
        self.displayed = displayed
        self.username = username
        self.rating = rating
        self.time = time
        self.proposal = proposal
        self.proposal_diff = proposal_diff

    def set_path(self, node_id, parent_id):
        if node_id:
            self.path = '%s.%s' % (node_id, self.id)
        else:
            session = Session()
            parent_path = session.query(Comment.path).\
                filter(Comment.id == parent_id).one().path
            session.close()
            self.path = '%s.%s' %  (parent_path, self.id)

    def serializable(self, vote=0):
        delta = datetime.now() - self.time

        time = {'year': self.time.year,
                'month': self.time.month,
                'day': self.time.day,
                'hour': self.time.hour,
                'minute': self.time.minute,
                'second': self.time.second,
                'iso': self.time.isoformat(),
                'delta': self.pretty_delta(delta)}

        path = self.path.split('.')
        node = path[0] if len(path) == 2 else None
        parent = path[-2] if len(path) > 2 else None

        return {'text': self.text,
                'username': self.username or 'Anonymous',
                'id': self.id,
                'node': node,
                'parent': parent,
                'rating': self.rating,
                'age': delta.seconds,
                'time': time,
                'vote': vote or 0,
                'proposal_diff': self.proposal_diff,
                'children': []}

    def pretty_delta(self, delta):
        days = delta.days
        seconds = delta.seconds
        hours = seconds / 3600
        minutes = seconds / 60

        if days == 0:
            dt = (minutes, 'minute') if hours == 0 else (hours, 'hour')
        else:
            dt = (days, 'day')

        return '%s %s ago' % dt if dt[0] == 1 else '%s %ss ago' % dt

class CommentVote(Base):
    __tablename__ = db_prefix + 'commentvote'

    username = Column(String(64), primary_key=True)
    comment_id = Column(Integer, ForeignKey(db_prefix + 'comments.id'),
                        primary_key=True)
    comment = relation(Comment, backref="votes")
    # -1 if downvoted, +1 if upvoted, 0 if voted then unvoted.
    value = Column(Integer, nullable=False)

    def __init__(self, comment_id, username, value):
        self.comment_id = comment_id
        self.username = username
        self.value = value
