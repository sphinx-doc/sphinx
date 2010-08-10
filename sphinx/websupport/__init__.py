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
from sphinx.websupport.storage import StorageBackend
from sphinx.websupport.errors import *

class WebSupportApp(Sphinx):
    def __init__(self, *args, **kwargs):
        self.staticdir = kwargs.pop('staticdir', None)
        self.builddir = kwargs.pop('builddir', None)
        self.search = kwargs.pop('search', None)
        self.storage = kwargs.pop('storage', None)
        Sphinx.__init__(self, *args, **kwargs)

class WebSupport(object):
    """The main API class for the web support package. All interactions
    with the web support package should occur through this class.
    """
    def __init__(self, srcdir='', builddir='', datadir='', search=None,
                 storage=None, status=sys.stdout, warning=sys.stderr,
                 moderation_callback=None, staticdir='static',
                 docroot=''):
        self.srcdir = srcdir
        self.builddir = builddir
        self.outdir = path.join(builddir, 'data')
        self.datadir = datadir or self.outdir
        self.staticdir = staticdir.strip('/')
        self.docroot = docroot.strip('/')
        self.status = status
        self.warning = warning
        self.moderation_callback = moderation_callback

        self._init_templating()
        self._init_search(search)
        self._init_storage(storage)

        self._make_base_comment_options()

    def _init_storage(self, storage):
        if isinstance(storage, StorageBackend):
            self.storage = storage
        else:
            # If a StorageBackend isn't provided, use the default
            # SQLAlchemy backend.
            from sphinx.websupport.storage.sqlalchemystorage \
                import SQLAlchemyStorage
            from sqlalchemy import create_engine
            db_path = path.join(self.datadir, 'db', 'websupport.db')
            ensuredir(path.dirname(db_path))
            uri = storage or 'sqlite:///%s' % db_path
            engine = create_engine(uri)
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
            search_path = path.join(self.datadir, 'search')
            self.search = SearchClass(search_path)
        self.results_template = \
            self.template_env.get_template('searchresults.html')

    def build(self):
        """Build the documentation. Places the data into the `outdir`
        directory. Use it like this::

            support = WebSupport(srcdir, builddir, search='xapian')
            support.build()

        This will read reStructured text files from `srcdir`. Then it will
        build the pickles and search index, placing them into `builddir`.
        It will also save node data to the database.
        """
        if not self.srcdir:
            raise SrcdirNotSpecifiedError( \
                'No srcdir associated with WebSupport object')
        doctreedir = path.join(self.outdir, 'doctrees')
        app = WebSupportApp(self.srcdir, self.srcdir,
                            self.outdir, doctreedir, 'websupport',
                            search=self.search, status=self.status,
                            warning=self.warning, storage=self.storage,
                            staticdir=self.staticdir, builddir=self.builddir)

        self.storage.pre_build()
        app.build()
        self.storage.post_build()

    def get_document(self, docname, username='', moderator=False):
        """Load and return a document from a pickle. The document will
        be a dict object which can be used to render a template::

            support = WebSupport(datadir=datadir)
            support.get_document('index', username, moderator)

        In most cases `docname` will be taken from the request path and
        passed directly to this function. In Flask, that would be something
        like this::

            @app.route('/<path:docname>')
            def index(docname):
                username = g.user.name if g.user else ''
                moderator = g.user.moderator if g.user else False
                try:
                    document = support.get_document(docname, username,
                                                    moderator)
                except DocumentNotFoundError:
                    abort(404)
                render_template('doc.html', document=document)

        The document dict that is returned contains the following items
        to be used during template rendering.

        * **body**: The main body of the document as HTML
        * **sidebar**: The sidebar of the document as HTML
        * **relbar**: A div containing links to related documents
        * **title**: The title of the document
        * **css**: Links to css files used by Sphinx
        * **js**: Javascript containing comment options

        This raises :class:`~sphinx.websupport.errors.DocumentNotFoundError`
        if a document matching `docname` is not found.

        :param docname: the name of the document to load.
        """
        infilename = path.join(self.datadir, 'pickles', docname + '.fpickle')

        try:
            f = open(infilename, 'rb')
        except IOError:
            raise DocumentNotFoundError(
                'The document "%s" could not be found' % docname)

        document = pickle.load(f)
        comment_opts = self._make_comment_options(username, moderator)
        comment_metadata = self.storage.get_metadata(docname, moderator)

        document['js'] = '\n'.join([comment_opts,
                                    self._make_metadata(comment_metadata),
                                    document['js']])
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
        `username` is given vote information will be included with the
        returned comments. The default CommentBackend returns a dict with
        two keys, *source*, and *comments*. *source* is raw source of the
        node and is used as the starting point for proposals a user can
        add. *comments* is a list of dicts that represent a comment, each
        having the following items:

        ============= ======================================================
        Key           Contents
        ============= ======================================================
        text          The comment text.
        username      The username that was stored with the comment.
        id            The comment's unique identifier.
        rating        The comment's current rating.
        age           The time in seconds since the comment was added.
        time          A dict containing time information. It contains the
                      following keys: year, month, day, hour, minute, second,
                      iso, and delta. `iso` is the time formatted in ISO
                      8601 format. `delta` is a printable form of how old
                      the comment is (e.g. "3 hours ago").
        vote          If `user_id` was given, this will be an integer
                      representing the vote. 1 for an upvote, -1 for a
                      downvote, or 0 if unvoted.
        node          The id of the node that the comment is attached to.
                      If the comment's parent is another comment rather than
                      a node, this will be null.
        parent        The id of the comment that this comment is attached
                      to if it is not attached to a node.
        children      A list of all children, in this format.
        proposal_diff An HTML representation of the differences between the
                      the current source and the user's proposed source.
        ============= ======================================================

        :param node_id: the id of the node to get comments for.
        :param username: the username of the user viewing the comments.
        :param moderator: whether the user is a moderator.
        """
        return self.storage.get_data(node_id, username, moderator)

    def delete_comment(self, comment_id, username='', moderator=False):
        """Delete a comment. Doesn't actually delete the comment, but
        instead replaces the username and text files with "[deleted]" so
        as not to leave any comments orphaned.

        If `moderator` is True, the comment will always be deleted. If
        `moderator` is False, the comment will only be deleted if the
        `username` matches the `username` on the comment.

        This raises :class:`~sphinx.websupport.errors.UserNotAuthorizedError`
        if moderator is False and `username` doesn't match username on the
        comment.

        :param comment_id: the id of the comment to delete.
        :param username: the username requesting the deletion.
        :param moderator: whether the requestor is a moderator.
        """
        self.storage.delete_comment(comment_id, username, moderator)

    def add_comment(self, text, node_id='', parent_id='', displayed=True,
                    username=None, time=None, proposal=None,
                    moderator=False):
        """Add a comment to a node or another comment. Returns the comment
        in the same format as :meth:`get_comments`. If the comment is being
        attached to a node, pass in the node's id (as a string) with the
        node keyword argument::

            comment = support.add_comment(text, node_id=node_id)

        If the comment is the child of another comment, provide the parent's
        id (as a string) with the parent keyword argument::

            comment = support.add_comment(text, parent_id=parent_id)

        If you would like to store a username with the comment, pass
        in the optional `username` keyword argument::

            comment = support.add_comment(text, node=node_id,
                                          username=username)

        :param parent_id: the prefixed id of the comment's parent.
        :param text: the text of the comment.
        :param displayed: for moderation purposes
        :param username: the username of the user making the comment.
        :param time: the time the comment was created, defaults to now.
        """
        comment = self.storage.add_comment(text, displayed, username,
                                           time, proposal, node_id,
                                           parent_id, moderator)
        if not displayed and self.moderation_callback:
            self.moderation_callback(comment)
        return comment

    def process_vote(self, comment_id, username, value):
        """Process a user's vote. The web support package relies
        on the API user to perform authentication. The API user will
        typically receive a comment_id and value from a form, and then
        make sure the user is authenticated. A unique username  must be
        passed in, which will also be used to retrieve the user's past
        voting data. An example, once again in Flask::

            @app.route('/docs/process_vote', methods=['POST'])
            def process_vote():
                if g.user is None:
                    abort(401)
                comment_id = request.form.get('comment_id')
                value = request.form.get('value')
                if value is None or comment_id is None:
                    abort(400)
                support.process_vote(comment_id, g.user.name, value)
                return "success"

        :param comment_id: the comment being voted on
        :param username: the unique username of the user voting
        :param value: 1 for an upvote, -1 for a downvote, 0 for an unvote.
        """
        value = int(value)
        if not -1 <= value <= 1:
            raise ValueError('vote value %s out of range (-1, 1)' % value)
        self.storage.process_vote(comment_id, username, value)

    def update_username(self, old_username, new_username):
        """To remain decoupled from a webapp's authentication system, the
        web support package stores a user's username with each of their
        comments and votes. If the authentication system allows a user to
        change their username, this can lead to stagnate data in the web
        support system. To avoid this, each time a username is changed, this
        method should be called.

        :param old_username: The original username.
        :param new_username: The new username.
        """
        self.storage.update_username(old_username, new_username)

    def accept_comment(self, comment_id, moderator=False):
        """Accept a comment that is pending moderation.

        This raises :class:`~sphinx.websupport.errors.UserNotAuthorizedError`
        if moderator is False.

        :param comment_id: The id of the comment that was accepted.
        :param moderator: Whether the user making the request is a moderator.
        """
        if not moderator:
            raise UserNotAuthorizedError()
        self.storage.accept_comment(comment_id)

    def reject_comment(self, comment_id, moderator=False):
        """Reject a comment that is pending moderation.

        This raises :class:`~sphinx.websupport.errors.UserNotAuthorizedError`
        if moderator is False.

        :param comment_id: The id of the comment that was accepted.
        :param moderator: Whether the user making the request is a moderator.
        """
        if not moderator:
            raise UserNotAuthorizedError()
        self.storage.reject_comment(comment_id)

    def _make_base_comment_options(self):
        """Helper method to create the part of the COMMENT_OPTIONS javascript
        that remains the same throughout the lifetime of the
        :class:`~sphinx.websupport.WebSupport` object.
        """
        parts = ['<script type="text/javascript">',
                 'var COMMENT_OPTIONS = {']
        if self.docroot is not '':
            parts.append('addCommentURL: "/%s/%s",' % (self.docroot,
                                                       'add_comment'))
            parts.append('getCommentsURL: "/%s/%s",' % (self.docroot,
                                                        'get_comments'))
            parts.append('processVoteURL: "/%s/%s",' % (self.docroot,
                                                        'process_vote'))
            parts.append('acceptCommentURL: "/%s/%s",' % (self.docroot,
                                                          'accept_comment'))
            parts.append('rejectCommentURL: "/%s/%s",' % (self.docroot,
                                                          'reject_comment'))
            parts.append('deleteCommentURL: "/%s/%s",' % (self.docroot,
                                                          'delete_comment'))

        if self.staticdir != 'static':
            p = lambda file: '%s/_static/%s' % (self.staticdir, file)
            parts.append('commentImage: "/%s",' % p('comment.png') )
            parts.append(
                'commentBrightImage: "/%s",' % p('comment-bright.png') )
            parts.append('upArrow: "/%s",' % p('up.png'))
            parts.append('downArrow: "/%s",' % p('down.png'))
            parts.append('upArrowPressed: "/%s",' % p('up-pressed.png'))
            parts.append('downArrowPressed: "/%s",' % p('down-pressed.png'))

        self.base_comment_opts = '\n'.join(parts)

    def _make_comment_options(self, username, moderator):
        """Helper method to create the parts of the COMMENT_OPTIONS
        javascript that are unique to each request.

        :param username: The username of the user making the request.
        :param moderator: Whether the user making the request is a moderator.
        """
        parts = [self.base_comment_opts]
        if username is not '':
            parts.append('voting: true,')
            parts.append('username: "%s",' % username)
        parts.append('moderator: %s' % str(moderator).lower())
        parts.append('};')
        parts.append('</script>')
        return '\n'.join(parts)

    def _make_metadata(self, data):
        node_js = ', '.join(['%s: %s' % (node_id, comment_count)
                             for node_id, comment_count in data.iteritems()])
        js = """
<script type="text/javascript">
  var COMMENT_METADATA = {%s};
</script>""" % node_js
        return js
