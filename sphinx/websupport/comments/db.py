from sqlalchemy import Column, Integer, Text, String, Boolean, ForeignKey,\
DateTime
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

    def __repr__(self):
        return '<Node %s#%s>' % (document, treeloc)

class Comment(Base):
    __tablename__ = db_prefix + 'comments'

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    text = Column(Text, nullable=False)
    displayed = Column(Boolean, index=True, default=False)
    user_id = Column(String(50), nullable=True)

    node_id = Column(Integer, ForeignKey(db_prefix + 'nodes.id'))
    node = relation(Node, backref='comments')

    parent_id = Column(Integer, ForeignKey(db_prefix + 'comments.id'))
    parent = relation('Comment', backref='children', remote_side=[id])

    def __init__(self, text, displayed, user_id, rating, time, 
                 node=None, parent=None):
        self.text = text
        self.displayed = displayed
        self.user_id = user_id
        self.rating = rating
        self.time = time
        self.node = node
        self.parent = parent
