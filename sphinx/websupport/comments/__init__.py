from datetime import datetime

from sqlalchemy.orm import sessionmaker

from sphinx.websupport.comments.db import Base, Node, Comment

Session = sessionmaker()

class CommentBackend(object):
    def pre_build(self):
        pass

    def add_node(self, document, line, source, treeloc):
        raise NotImplemented
    
    def post_build(self):
        pass

    def add_comment(self, parent_id, text, displayed, user_id, rating, time):
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

    def add_node(self, document, line, source, treeloc):
        node = Node(document, line, source, treeloc)
        self.session.add(node)
        return node.id

    def post_build(self):
        self.session.commit()

    def add_comment(self, parent_id, text, displayed, user_id, rating, time):
        time = time or datetime.now()

        id = parent_id[1:]
        if parent_id[0] == 's':
            node = self.session.query(Node).filter(Node.id == id).first()
            comment = Comment(text, displayed, user_id, rating, 
                              time, node=node)
        elif parent_id[0] == 'c':
            parent = self.session.query(Comment).filter(Comment.id == id).first()
            comment = Comment(text, displayed, user_id, rating, 
                              time, parent=parent)
            
        self.session.add(comment)
        self.session.commit()
        return self.serializable(comment)
        
    def get_comments(self, parent_id):
        parent_id = parent_id[1:]
        node = self.session.query(Node).filter(Node.id == parent_id).first()
        comments = []
        for comment in node.comments:
            comments.append(self.serializable(comment))

        return comments

    def serializable(self, comment):
        time = {'year': comment.time.year,
                'month': comment.time.month,
                'day': comment.time.day,
                'hour': comment.time.hour,
                'minute': comment.time.minute,
                'second': comment.time.second,
                'iso': comment.time.isoformat(),
                'delta': self.pretty_delta(comment)}

        return {'text': comment.text,
                'user_id': comment.user_id,
                'id': comment.id,
                'rating': self.pretty_rating(comment),
                'time': time,
                'node': comment.node.id if comment.node else None,
                'parent': comment.parent.id if comment.parent else None,
                'children': [self.serializable(child) 
                             for child in comment.children]}

    def pretty_rating(self, comment):
        if comment.rating == 1:
            return '%s point' % comment.rating
        else:
            return '%s points' % comment.rating

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
