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
from sqlalchemy.orm import relation, sessionmaker

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

    #node_id = Column(Integer, ForeignKey(db_prefix + 'nodes.id'))
    #node = relation(Node, backref='comments')

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

        return {'text': self.text,
                'username': self.username or 'Anonymous',
                'id': self.id,
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
