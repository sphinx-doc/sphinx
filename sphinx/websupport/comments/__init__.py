from datetime import datetime

from sqlalchemy.orm import sessionmaker

from sphinx.websupport.comments.db import Base, Node, Comment, Vote

Session = sessionmaker()

class CommentBackend(object):
    def pre_build(self):
        pass

    def add_node(self, document, line, source, treeloc):
        raise NotImplemented
    
    def post_build(self):
        pass

    def add_comment(self, parent_id, text, displayed, username, 
                    rating, time):
        raise NotImplemented

    def get_comments(self, parent_id):
        raise NotImplemented


class SQLAlchemyComments(CommentBackend):
    def __init__(self, engine):
        self.engine = engine
        Base.metadata.bind = engine
        Base.metadata.create_all()
        Session.configure(bind=engine)
        self.session = Session()

    def pre_build(self):
        self.current_pk = None

    def add_node(self, document, line, source, treeloc):
        node = Node(document, line, source, treeloc)
        self.session.add(node)
        if self.current_pk is None:
            self.session.commit()
            self.current_pk = node.id
        else:
            self.current_pk += 1
        return self.current_pk

    def post_build(self):
        self.session.commit()

    def add_comment(self, parent_id, text, displayed, 
                    username, rating, time):
        time = time or datetime.now()

        id = parent_id[1:]
        if parent_id[0] == 's':
            node = self.session.query(Node).filter(Node.id == id).first()
            comment = Comment(text, displayed, username, rating, 
                              time, node=node)
        elif parent_id[0] == 'c':
            parent = self.session.query(Comment).filter(Comment.id == id).first()
            comment = Comment(text, displayed, username, rating, 
                              time, parent=parent)
            
        self.session.add(comment)
        self.session.commit()
        return self.serializable(comment)
        
    def get_comments(self, parent_id, user_id):
        parent_id = parent_id[1:]
        node = self.session.query(Node).filter(Node.id == parent_id).first()
        comments = []
        for comment in node.comments:
            comments.append(self.serializable(comment, user_id))

        return comments

    def process_vote(self, comment_id, user_id, value):
        vote = self.session.query(Vote).filter(
            Vote.comment_id == comment_id).filter(
            Vote.user_id == user_id).first()
        
        comment = self.session.query(Comment).filter(
            Comment.id == comment_id).first()

        if vote is None:
            vote = Vote(comment_id, user_id, value)
            comment.rating += value
        else:
            comment.rating += value - vote.value
            vote.value = value
        self.session.add(vote)
        self.session.commit()

    def serializable(self, comment, user_id=None):
        time = {'year': comment.time.year,
                'month': comment.time.month,
                'day': comment.time.day,
                'hour': comment.time.hour,
                'minute': comment.time.minute,
                'second': comment.time.second,
                'iso': comment.time.isoformat(),
                'delta': self.pretty_delta(comment)}

        vote = ''
        if user_id is not None:
            vote = self.session.query(Vote).filter(
                Vote.comment_id == comment.id).filter(
                Vote.user_id == user_id).first()
            if vote is not None:
                vote = vote.value 

        return {'text': comment.text,
                'username': comment.username or 'Anonymous',
                'id': comment.id,
                'rating': comment.rating,
                'time': time,
                'vote': vote or 0,
                'node': comment.node.id if comment.node else None,
                'parent': comment.parent.id if comment.parent else None,
                'children': [self.serializable(child, user_id) 
                             for child in comment.children]}

    def pretty_delta(self, comment):
        delta = datetime.now() - comment.time
        days = delta.days
        seconds = delta.seconds
        hours = seconds / 3600
        minutes = seconds / 60

        if days == 0:
            dt = (minutes, 'minute') if hours == 0 else (hours, 'hour')
        else:
            dt = (days, 'day')

        return '%s %s ago' % dt if dt[0] == 1 else '%s %ss ago' % dt
