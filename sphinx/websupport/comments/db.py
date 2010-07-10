from sqlalchemy import Column, Integer, Text, String, Boolean, ForeignKey,\
DateTime
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation

Base = declarative_base()

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

    node_id = Column(Integer, ForeignKey(db_prefix + 'nodes.id'))
    node = relation(Node, backref='comments')

    parent_id = Column(Integer, ForeignKey(db_prefix + 'comments.id'))
    parent = relation('Comment', backref='children', remote_side=[id])

    def __init__(self, text, displayed, username, rating, time, 
                 node=None, parent=None):
        self.text = text
        self.displayed = displayed
        self.username = username
        self.rating = rating
        self.time = time
        self.node = node
        self.parent = parent

class Vote(Base):
    __tablename__ = db_prefix + 'vote'

    id = Column(Integer, primary_key=True)
    # -1 if downvoted, +1 if upvoted, 0 if voted then unvoted.
    value = Column(Integer, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)

    comment_id = Column(Integer, ForeignKey(db_prefix + 'comments.id'),
                        nullable=False)
    comment = relation(Comment, backref="votes")

    __table_args__ = (UniqueConstraint(comment_id, user_id), {}) 

    def __init__(self, comment_id, user_id, value):
        self.value = value
        self.user_id = user_id
        self.comment_id = comment_id
    
