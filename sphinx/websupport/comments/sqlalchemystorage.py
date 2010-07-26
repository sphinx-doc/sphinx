from datetime import datetime

from sphinx.websupport.comments import StorageBackend
from sphinx.websupport.comments.db import Base, Node, Comment, CommentVote, Session

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

    def add_comment(self, parent_id, text, displayed, 
                    username, rating, time, proposal):
        time = time or datetime.now()
        
        session = Session()
        
        id = parent_id[1:]
        if parent_id[0] == 's':
            node = session.query(Node).filter(Node.id == id).first()
            comment = Comment(text, displayed, username, rating, 
                              time, proposal, node=node)
        elif parent_id[0] == 'c':
            parent = session.query(Comment).filter(Comment.id == id).first()
            comment = Comment(text, displayed, username, rating, 
                              time,proposal, parent=parent)
            
        session.add(comment)
        session.commit()
        comment = comment.serializable()
        session.close()
        return comment
        
    def get_comments(self, parent_id, user_id):
        parent_id = parent_id[1:]
        session = Session()
        node = session.query(Node).filter(Node.id == parent_id).first()
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

