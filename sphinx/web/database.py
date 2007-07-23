# -*- coding: utf-8 -*-
"""
    sphinx.web.database
    ~~~~~~~~~~~~~~~~~~~

    The database connections are thread local. To set the connection
    for a thread use the `set_connection` function provided. The
    `connect` method automatically sets up new tables and returns a
    usable connection which is also set as the connection for the
    thread that called that function.

    :copyright: 2007 by Georg Brandl, Armin Ronacher.
    :license: Python license.
"""
import time
import sqlite3
from datetime import datetime
from threading import local

from .markup import markup


_thread_local = local()


def connect(path):
    """Connect and create tables if required. Also assigns
    the connection for the current thread."""
    con = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    con.isolation_level = None

    # create tables that do not exist.
    for table in tables:
        try:
            con.execute('select * from %s limit 1;' % table)
        except sqlite3.OperationalError:
            con.execute(tables[table])

    set_connection(con)
    return con


def get_cursor():
    """Return a new cursor."""
    return _thread_local.connection.cursor()


def set_connection(con):
    """Call this after thread creation to make this connection
    the connection for this thread."""
    _thread_local.connection = con


#: tables that we use
tables = {
    'comments': '''
        create table comments (
            comment_id integer primary key,
            associated_page varchar(200),
            associated_name varchar(200),
            title varchar(120),
            author varchar(200),
            author_mail varchar(250),
            comment_body text,
            pub_date timestamp
        );'''
}


class Comment(object):
    """
    Represents one comment.
    """

    def __init__(self, associated_page, associated_name, title, author,
                 author_mail, comment_body, pub_date=None):
        self.comment_id = None
        self.associated_page = associated_page
        self.associated_name = associated_name
        self.title = title
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.author = author
        self.author_mail = author_mail
        self.comment_body = comment_body

    @property
    def url(self):
        return '%s#comment-%s' % (
            self.associated_page[:-4],
            self.comment_id
        )

    @property
    def parsed_comment_body(self):
        from .util import get_target_uri
        from ..util import relative_uri
        uri = get_target_uri(self.associated_page)
        def make_rel_link(keyword):
            return relative_uri(uri, 'q/%s/' % keyword)
        return markup(self.comment_body, make_rel_link)

    def save(self):
        """
        Save the comment and use the cursor provided.
        """
        cur = get_cursor()
        args = (self.associated_page, self.associated_name, self.title,
                self.author, self.author_mail, self.comment_body, self.pub_date)
        if self.comment_id is None:
            cur.execute('''insert into comments (associated_page, associated_name,
                                                 title,
                                                 author, author_mail,
                                                 comment_body, pub_date)
                                  values (?, ?, ?, ?, ?, ?, ?)''', args)
            self.comment_id = cur.lastrowid
        else:
            args += (self.comment_id,)
            cur.execute('''update comments set associated_page=?,
                                  associated_name=?,
                                  title=?, author=?,
                                  author_mail=?, comment_body=?,
                                  pub_date=? where comment_id = ?''', args)
        cur.close()

    def delete(self):
        cur = get_cursor()
        cur.execute('delete from comments where comment_id = ?',
                    (self.comment_id,))
        cur.close()

    @staticmethod
    def _make_comment(row):
        rv = Comment(*row[1:])
        rv.comment_id = row[0]
        return rv

    @staticmethod
    def get(comment_id):
        cur = get_cursor()
        cur.execute('select * from comments where comment_id = ?', (comment_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError('comment not found')
        try:
            return Comment._make_comment(row)
        finally:
            cur.close()

    @staticmethod
    def get_for_page(associated_page, reverse=False):
        cur = get_cursor()
        cur.execute('''select * from comments where associated_page = ?
                    order by associated_name, comment_id %s''' %
                     ('desc' if reverse else 'asc'),
                    (associated_page,))
        try:
            return [Comment._make_comment(row) for row in cur]
        finally:
            cur.close()

    @staticmethod
    def get_recent(n=10):
        cur = get_cursor()
        cur.execute('select * from comments order by comment_id desc limit ?',
                    (n,))
        try:
            return [Comment._make_comment(row) for row in cur]
        finally:
            cur.close()

    @staticmethod
    def get_overview(detail_for=None):
        cur = get_cursor()
        cur.execute('''select distinct associated_page from comments
                              order by associated_page asc''')
        pages = []
        for row in cur:
            page_id = row[0]
            if page_id == detail_for:
                pages.append((page_id, Comment.get_for_page(page_id, True)))
            else:
                pages.append((page_id, []))
        cur.close()
        return pages

    def __repr__(self):
        return '<Comment by %r on %r:%r (%s)>' % (
            self.author,
            self.associated_page,
            self.associated_name,
            self.comment_id or 'not saved'
        )
