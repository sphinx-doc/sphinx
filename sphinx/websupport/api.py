# -*- coding: utf-8 -*-
"""
    sphinx.websupport.api
    ~~~~~~~~~~~~~~~~~~~~~

    All API functions.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import cPickle as pickle
from os import path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from sphinx.application import Sphinx
from sphinx.util.osutil import ensuredir
from sphinx.websupport.search import search_adapters
from sphinx.websupport import comments as sphinxcomments

class WebSupportApp(Sphinx):
    def __init__(self, *args, **kwargs):
        self.search = kwargs.pop('search', None)
        self.comments = kwargs.pop('comments', None)
        Sphinx.__init__(self, *args, **kwargs)

class WebSupport(object):
    def __init__(self, srcdir='', outdir='', search=None,
                 comments=None):
        self.srcdir = srcdir
        self.outdir = outdir or path.join(self.srcdir, '_build',
                                          'websupport')
        self.init_templating()
        if search is not None:
            self.init_search(search)

        self.init_comments(comments)
    
    def init_comments(self, comments):
        if isinstance(comments, sphinxcomments.CommentBackend):
            self.comments = comments
        else:
            # If a CommentBackend isn't provided, use the default
            # SQLAlchemy backend with an SQLite db.
            from sphinx.websupport.comments import SQLAlchemyComments
            from sqlalchemy import create_engine
            db_path = path.join(self.outdir, 'comments', 'comments.db')
            ensuredir(path.dirname(db_path))
            engine = create_engine('sqlite:///%s' % db_path)
            self.comments = SQLAlchemyComments(engine)
        
    def init_templating(self):
        import sphinx
        template_path = path.join(path.dirname(sphinx.__file__),
                                  'themes', 'basic')
        loader = FileSystemLoader(template_path)
        self.template_env = Environment(loader=loader)

    def init_search(self, search):
        mod, cls = search_adapters[search]
        search_class = getattr(__import__('sphinx.websupport.search.' + mod, 
                                          None, None, [cls]), cls)
        search_path = path.join(self.outdir, 'search')
        self.search = search_class(search_path)
        self.results_template = \
            self.template_env.get_template('searchresults.html')

    def build(self, **kwargs):
        doctreedir = kwargs.pop('doctreedir', 
                                path.join(self.outdir, 'doctrees'))
        app = WebSupportApp(self.srcdir, self.srcdir,
                            self.outdir, doctreedir, 'websupport',
                            search=self.search,
                            comments=self.comments)
        self.comments.pre_build()
        app.build()
        self.comments.post_build()

    def get_document(self, docname):
        infilename = path.join(self.outdir, docname + '.fpickle')
        f = open(infilename, 'rb')
        document = pickle.load(f)
        return document

    def get_search_results(self, q):
        results, results_found, results_displayed = self.search.query(q)
        ctx = {'search_performed': True,
               'search_results': results,
               'q': q}
        document = self.get_document('search')
        document['body'] = self.results_template.render(ctx)
        document['title'] = 'Search Results'
        return document

    def get_comments(self, node_id, user_id):
        return self.comments.get_comments(node_id, user_id)

    def add_comment(self, parent_id, text, displayed=True, username=None,
                    rating=0, time=None):
        return self.comments.add_comment(parent_id, text, displayed, 
                                         username, rating, time)
    
    def process_vote(self, comment_id, user_id, value):
        value = int(value)
        self.comments.process_vote(comment_id, user_id, value)
