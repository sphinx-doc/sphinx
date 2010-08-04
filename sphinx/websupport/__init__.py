# -*- coding: utf-8 -*-
"""
    sphinx.websupport
    ~~~~~~~~~~~~~~~~~

    Base Module for web support functions.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import cPickle as pickle
from os import path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from sphinx.application import Sphinx
from sphinx.util.osutil import ensuredir
from sphinx.websupport.search import BaseSearch, search_adapters
from sphinx.websupport.comments import StorageBackend
from sphinx.websupport.errors import *

class WebSupportApp(Sphinx):
    def __init__(self, *args, **kwargs):
        self.search = kwargs.pop('search', None)
        self.storage = kwargs.pop('storage', None)
        Sphinx.__init__(self, *args, **kwargs)

class WebSupport(object):
    """The main API class for the web support package. All interactions
    with the web support package should occur through this class.
    """

    def __init__(self, srcdir='', outdir='', datadir='', search=None,
                 storage=None, status=sys.stdout, warning=sys.stderr):
        self.srcdir = srcdir
        self.outdir = outdir or path.join(self.srcdir, '_build',
                                          'websupport')
        self._init_templating()

        self.outdir = outdir or datadir

        self.status = status
        self.warning = warning

        self._init_search(search)            
        self._init_storage(storage)

    def _init_storage(self, storage):
        if isinstance(storage, StorageBackend):
            self.storage = storage
        else:
            # If a StorageBackend isn't provided, use the default
            # SQLAlchemy backend with an SQLite db.
            from sphinx.websupport.comments.sqlalchemystorage \
                import SQLAlchemyStorage
            from sqlalchemy import create_engine
            db_path = path.join(self.outdir, 'db', 'websupport.db')
            ensuredir(path.dirname(db_path))
            engine = create_engine('sqlite:///%s' % db_path)
            self.storage = SQLAlchemyStorage(engine)

    def _init_templating(self):
        import sphinx
        template_path = path.join(path.dirname(sphinx.__file__),
                                  'themes', 'basic')
        loader = FileSystemLoader(template_path)
        self.template_env = Environment(loader=loader)

    def _init_search(self, search):
        if isinstance(search, BaseSearch):
            self.search = search
        else:
            mod, cls = search_adapters[search or 'null']
            mod = 'sphinx.websupport.search.' + mod
            SearchClass = getattr(__import__(mod, None, None, [cls]), cls)
            search_path = path.join(self.outdir, 'search')
            self.search = SearchClass(search_path)
        self.results_template = \
            self.template_env.get_template('searchresults.html')

    def build(self):
        """Build the documentation. Places the data into the `outdir`
        directory. Use it like this::

            support = WebSupport(srcdir, outdir, search)
            support.build()

        This will read reStructured text files from `srcdir`. Then it
        build the pickles and search index, placing them into `outdir`.
        It will also save node data to the database.
        """
        if not self.srcdir:
            raise SrcdirNotSpecifiedError( \
                'No srcdir associated with WebSupport object')
        doctreedir = path.join(self.outdir, 'doctrees')
        app = WebSupportApp(self.srcdir, self.srcdir,
                            self.outdir, doctreedir, 'websupport',
                            search=self.search, status=self.status, 
                            warning=self.warning, storage=self.storage)

        self.storage.pre_build()
        app.build()
        self.storage.post_build()

    def get_document(self, docname):
        """Load and return a document from a pickle. The document will
        be a dict object which can be used to render a template::

            support = WebSupport(outdir=outdir)
            support.get_document('index')
            
        In most cases `docname` will be taken from the request path and 
        passed directly to this function. In Flask, that would be something
        like this::

            @app.route('/<path:docname>')
            def index(docname):
                q = request.args.get('q')
                document = support.get_search_results(q)
                render_template('doc.html', document=document)

        The document dict that is returned contains the following items
        to be used during template rendering.

        :param docname: the name of the document to load.
        """
        infilename = path.join(self.outdir, docname + '.fpickle')

        try:
            f = open(infilename, 'rb')
        except IOError:
            raise DocumentNotFoundError(
                'The document "%s" could not be found' % docname)

        document = pickle.load(f)
        return document

    def get_search_results(self, q):
        """Perform a search for the query `q`, and create a set
        of search results. Then render the search results as html and
        return a context dict like the one created by
        :meth:`get_document`::
        
            document = support.get_search_results(q)

        :param q: the search query
        """
        results = self.search.query(q)
        ctx = {'search_performed': True,
               'search_results': results,
               'q': q}
        document = self.get_document('search')
        document['body'] = self.results_template.render(ctx)
        document['title'] = 'Search Results'
        return document

    def get_data(self, node_id, username=None, moderator=False):
        """Get the comments and source associated with `node_id`. If 
        `user_id` is given vote information will be included with the 
        returned comments. The default CommentBackend returns dict with
        two keys, *source*, and *comments*. *comments* is a list of
        dicts that represent a comment, each having the following items:

        ============ ======================================================
        Key          Contents
        ============ ======================================================
        text         The comment text.
        username     The username that was stored with the comment.
        id           The comment's unique identifier.
        rating       The comment's current rating.
        age          The time in seconds since the comment was added.
        time         A dict containing time information. It contains the
                     following keys: year, month, day, hour, minute, second,
                     iso, and delta. `iso` is the time formatted in ISO
                     8601 format. `delta` is a printable form of how old
                     the comment is (e.g. "3 hours ago").
        vote         If `user_id` was given, this will be an integer
                     representing the vote. 1 for an upvote, -1 for a 
                     downvote, or 0 if unvoted.
        node         The node that the comment is attached to. If the
                     comment's parent is another comment rather than a
                     node, this will be null.
        parent       The id of the comment that this comment is attached 
                     to if it is not attached to a node.
        children     A list of all children, in this format.
        ============ ======================================================

        :param node_id: the id of the node to get comments for.
        :param user_id: the id of the user viewing the comments.
        """
        return self.storage.get_data(node_id, username, moderator)

    def add_comment(self, text, node_id='', parent_id='', displayed=True, 
                    username=None, rating=0, time=None, proposal=None,
                    moderator=False):
        """Add a comment to a node or another comment. Returns the comment 
        in the same format as :meth:`get_comments`. If the comment is being 
        attached to a node, pass in the node's id (as a string) with the 
        node keyword argument::

            comment = support.add_comment(text, node=node_id)

        If the comment is the child of another comment, provide the parent's
        id (as a string) with the parent keyword argument::
            
            comment = support.add_comment(text, parent=parent_id)

        If you would like to store a username with the comment, pass
        in the optional `username` keyword argument::

            comment = support.add_comment(text, node=node_id, 
                                          username=username)

        :param parent_id: the prefixed id of the comment's parent.
        :param text: the text of the comment.
        :param displayed: for moderation purposes
        :param username: the username of the user making the comment.
        :param rating: the starting rating of the comment, defaults to 0.
        :param time: the time the comment was created, defaults to now.
        """
        return self.storage.add_comment(text, displayed, username, rating,
                                        time, proposal, node_id, parent_id, 
                                        moderator)

    def process_vote(self, comment_id, username, value):
        """Process a user's vote. The web support package relies
        on the API user to perform authentication. The API user will 
        typically receive a comment_id and value from a form, and then
        make sure the user is authenticated. A unique integer `user_id` 
        (usually the User primary key) must be passed in, which will 
        also be used to retrieve the user's past voting information. 
        An example, once again in Flask::

            @app.route('/docs/process_vote', methods=['POST'])
            def process_vote():
                if g.user is None:
                    abort(401)
                comment_id = request.form.get('comment_id')
                value = request.form.get('value')
                if value is None or comment_id is None:
                    abort(400)
                support.process_vote(comment_id, g.user.id, value)
                return "success"

        :param comment_id: the comment being voted on
        :param user_id: the unique integer id of the user voting
        :param value: 1 for an upvote, -1 for a downvote, 0 for an unvote.
        """
        value = int(value)
        if not -1 <= value <= 1:
            raise ValueError('vote value %s out of range (-1, 1)' % value)
        self.storage.process_vote(comment_id, username, value)
