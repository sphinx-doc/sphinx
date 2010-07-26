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
    treeloc = Column(String(32), nullable=False)
    
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

    node_id = Column(Integer, ForeignKey(db_prefix + 'nodes.id'))
    node = relation(Node, backref='comments')

    parent_id = Column(Integer, ForeignKey(db_prefix + 'comments.id'))
    parent = relation('Comment', backref='children', remote_side=[id])

    def __init__(self, text, displayed, username, rating, time, 
                 proposal, node=None, parent=None):
        self.text = text
        self.displayed = displayed
        self.username = username
        self.rating = rating
        self.time = time
        self.node = node
        self.parent = parent
        self.proposal = proposal

    def serializable(self, user_id=None):
        delta = datetime.now() - self.time

        time = {'year': self.time.year,
                'month': self.time.month,
                'day': self.time.day,
                'hour': self.time.hour,
                'minute': self.time.minute,
                'second': self.time.second,
                'iso': self.time.isoformat(),
                'delta': self.pretty_delta(delta)}

        vote = ''
        if user_id is not None:
            session = Session()
            vote = session.query(CommentVote).filter(
                CommentVote.comment_id == self.id).filter(
                CommentVote.user_id == user_id).first()
            vote = vote.value if vote is not None else 0
            session.close()

        return {'text': self.text,
                'username': self.username or 'Anonymous',
                'id': self.id,
                'rating': self.rating,
                'age': delta.seconds,
                'time': time,
                'vote': vote or 0,
                'node': self.node.id if self.node else None,
                'parent': self.parent.id if self.parent else None,
                'children': [child.serializable(user_id) 
                             for child in self.children]}

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

    user_id = Column(Integer, primary_key=True)
    # -1 if downvoted, +1 if upvoted, 0 if voted then unvoted.
    value = Column(Integer, nullable=False)

    comment_id = Column(Integer, ForeignKey(db_prefix + 'comments.id'),
                        primary_key=True)
    comment = relation(Comment, backref="votes")

    def __init__(self, comment_id, user_id, value):
        self.value = value
        self.user_id = user_id
        self.comment_id = comment_id
