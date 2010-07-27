# -*- coding: utf-8 -*-
"""
    sphinx.websupport
    ~~~~~~~~~~~~~~~~~

    Base Module for web support functions.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import cPickle as pickle
import re
from os import path
from cgi import escape
from difflib import Differ
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from sphinx.application import Sphinx
from sphinx.util.osutil import ensuredir
from sphinx.websupport.search import BaseSearch, search_adapters
from sphinx.websupport.comments import StorageBackend

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
                 storage=None):
        self.srcdir = srcdir
        self.outdir = outdir or path.join(self.srcdir, '_build',
                                          'websupport')
        self._init_templating()

        self.outdir = outdir or datadir

        if search is not None:
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
            mod, cls = search_adapters[search]
            search_class = getattr(__import__('sphinx.websupport.search.' + mod,
                                          None, None, [cls]), cls)
            search_path = path.join(self.outdir, 'search')
            self.search = search_class(search_path)
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
        doctreedir = path.join(self.outdir, 'doctrees')
        app = WebSupportApp(self.srcdir, self.srcdir,
                            self.outdir, doctreedir, 'websupport',
                            search=self.search,
                            storage=self.storage)

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
        f = open(infilename, 'rb')
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

    def get_comments(self, node_id, user_id=None):
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
        return self.storage.get_comments(node_id, user_id)

    def add_comment(self, parent_id, text, displayed=True, username=None,
                    rating=0, time=None, proposal=None):
        """Add a comment to a node or another comment. `parent_id` will have
        a one letter prefix, distinguishing between node parents and 
        comment parents, 'c' and 's' respectively. This function will
        return the comment in the same format as :meth:`get_comments`.
        Usage is simple::

            comment = support.add_comment(parent_id, text)
        
        If you would like to store a username with the comment, pass
        in the optional `username` keyword argument::

            comment = support.add_comment(parent_id, text, username=username)

        :param parent_id: the prefixed id of the comment's parent.
        :param text: the text of the comment.
        :param displayed: for future use...
        :param username: the username of the user making the comment.
        :param rating: the starting rating of the comment, defaults to 0.
        :param time: the time the comment was created, defaults to now.
        """
        id = parent_id[1:]
        is_node = parent_id[0] == 's'
        node = self.storage.get_node(id) if is_node else None
        parent = self.storage.get_comment(id) if not is_node else None
        diff = get_diff_html(node.source, proposal) if proposal else None
        return self.storage.add_comment(text, displayed, username, rating,
                                        time, proposal, diff, node, parent)

    def process_vote(self, comment_id, user_id, value):
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
        self.storage.process_vote(comment_id, user_id, value)

highlight_regex = re.compile(r'([\+\-\^]+)')

def highlight_text(text, next, tag):
    next = next[2:]
    new_text = []
    start = 0
    for match in highlight_regex.finditer(next):
        new_text.append(text[start:match.start()])
        new_text.append('<%s>' % tag)
        new_text.append(text[match.start():match.end()])
        new_text.append('</%s>' % tag)
        start = match.end()
    new_text.append(text[start:])
    return ''.join(new_text)

def get_diff_html(source, proposal):
    proposal = escape(proposal)

    def handle_line(line, next=None):
        prefix = line[0]
        text = line[2:]

        if prefix == ' ':
            return text
        elif prefix == '?':
            return ''
        
        if next[0] == '?':
            tag = 'ins' if prefix == '+' else 'del'
            text = highlight_text(text, next, tag)
        css_class = 'prop_added' if prefix == '+' else 'prop_removed'
        
        return '<span class="%s">%s</span>\n' % (css_class, text.rstrip())

    differ = Differ()
    diff = list(differ.compare(source.splitlines(1), proposal.splitlines(1)))

    html = []
    line = diff.pop(0)
    next = diff.pop(0)
    while True:
        html.append(handle_line(line, next))
        line = next
        try:
            next = diff.pop(0)
        except IndexError:
            handle_line(line)
            break

    return ''.join(html)

