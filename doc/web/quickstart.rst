.. _websupportquickstart:

Web Support Quick Start
=======================

Building Documentation Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make use of the web support package in your application you'll need to build
the data it uses.  This data includes pickle files representing documents,
search indices, and node data that is used to track where comments and other
things are in a document.  To do this you will need to create an instance of the
:class:`~.WebSupport` class and call its :meth:`~.WebSupport.build` method::

   from sphinx.websupport import WebSupport

   support = WebSupport(srcdir='/path/to/rst/sources/',
                        builddir='/path/to/build/outdir',
                        search='xapian')

   support.build()

This will read reStructuredText sources from `srcdir` and place the necessary
data in `builddir`.  The `builddir` will contain two sub-directories: one named
"data" that contains all the data needed to display documents, search through
documents, and add comments to documents.  The other directory will be called
"static" and contains static files that should be served from "/static".

.. note::

   If you wish to serve static files from a path other than "/static", you can
   do so by providing the *staticdir* keyword argument when creating the
   :class:`~.WebSupport` object.


Integrating Sphinx Documents Into Your Webapp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that the data is built, it's time to do something useful with it.  Start off
by creating a :class:`~.WebSupport` object for your application::

   from sphinx.websupport import WebSupport

   support = WebSupport(datadir='/path/to/the/data',
                        search='xapian')

You'll only need one of these for each set of documentation you will be working
with.  You can then call it's :meth:`~.WebSupport.get_document` method to access
individual documents::

   contents = support.get_document('contents')

This will return a dictionary containing the following items:

* **body**: The main body of the document as HTML
* **sidebar**: The sidebar of the document as HTML
* **relbar**: A div containing links to related documents
* **title**: The title of the document
* **css**: Links to css files used by Sphinx
* **js**: Javascript containing comment options

This dict can then be used as context for templates.  The goal is to be easy to
integrate with your existing templating system.  An example using `Jinja2
<http://jinja.pocoo.org/>`_ is:

.. sourcecode:: html+jinja

   {%- extends "layout.html" %}

   {%- block title %}
       {{ document.title }}
   {%- endblock %}

   {% block css %}
       {{ super() }}
       {{ document.css|safe }}
       <link rel="stylesheet" href="/static/websupport-custom.css" type="text/css">
   {% endblock %}

   {%- block js %}
       {{ super() }}
       {{ document.js|safe }}
   {%- endblock %}

   {%- block relbar %}
       {{ document.relbar|safe }}
   {%- endblock %}

   {%- block body %}
       {{ document.body|safe }}
   {%- endblock %}

   {%- block sidebar %}
       {{ document.sidebar|safe }}
   {%- endblock %}


Authentication
--------------

To use certain features such as voting, it must be possible to authenticate
users.  The details of the authentication are left to your application.  Once a
user has been authenticated you can pass the user's details to certain
:class:`~.WebSupport` methods using the *username* and *moderator* keyword
arguments.  The web support package will store the username with comments and
votes.  The only caveat is that if you allow users to change their username you
must update the websupport package's data::

   support.update_username(old_username, new_username)

*username* should be a unique string which identifies a user, and *moderator*
should be a boolean representing whether the user has moderation privilieges.
The default value for *moderator* is *False*.

An example `Flask <http://flask.pocoo.org/>`_ function that checks whether a
user is logged in and then retrieves a document is::

   from sphinx.websupport.errors import *

   @app.route('/<path:docname>')
   def doc(docname):
       username = g.user.name if g.user else ''
       moderator = g.user.moderator if g.user else False
       try:
           document = support.get_document(docname, username, moderator)
       except DocumentNotFoundError:
           abort(404)
       return render_template('doc.html', document=document)

The first thing to notice is that the *docname* is just the request path.  This
makes accessing the correct document easy from a single view.  If the user is
authenticated, then the username and moderation status are passed along with the
docname to :meth:`~.WebSupport.get_document`.  The web support package will then
add this data to the ``COMMENT_OPTIONS`` that are used in the template.

.. note::

   This only works works if your documentation is served from your
   document root. If it is served from another directory, you will
   need to prefix the url route with that directory, and give the `docroot`
   keyword argument when creating the web support object::

      support = WebSupport(..., docroot='docs')

      @app.route('/docs/<path:docname>')


Performing Searches
~~~~~~~~~~~~~~~~~~~

To use the search form built-in to the Sphinx sidebar, create a function to
handle requests to the url 'search' relative to the documentation root.  The
user's search query will be in the GET parameters, with the key `q`.  Then use
the :meth:`~sphinx.websupport.WebSupport.get_search_results` method to retrieve
search results. In `Flask <http://flask.pocoo.org/>`_ that would be like this::

   @app.route('/search')
   def search():
       q = request.args.get('q')
       document = support.get_search_results(q)
       return render_template('doc.html', document=document)

Note that we used the same template to render our search results as we did to
render our documents.  That's because :meth:`~.WebSupport.get_search_results`
returns a context dict in the same format that :meth:`~.WebSupport.get_document`
does.


Comments & Proposals
~~~~~~~~~~~~~~~~~~~~

Now that this is done it's time to define the functions that handle the AJAX
calls from the script.  You will need three functions.  The first function is
used to add a new comment, and will call the web support method
:meth:`~.WebSupport.add_comment`::

   @app.route('/docs/add_comment', methods=['POST'])
   def add_comment():
       parent_id = request.form.get('parent', '')
       node_id = request.form.get('node', '')
       text = request.form.get('text', '')
       proposal = request.form.get('proposal', '')
       username = g.user.name if g.user is not None else 'Anonymous'
       comment = support.add_comment(text, node_id='node_id',
                                     parent_id='parent_id',
                                     username=username, proposal=proposal)
       return jsonify(comment=comment)

You'll notice that both a `parent_id` and `node_id` are sent with the
request. If the comment is being attached directly to a node, `parent_id`
will be empty. If the comment is a child of another comment, then `node_id`
will be empty. Then next function handles the retrieval of comments for a
specific node, and is aptly named
:meth:`~sphinx.websupport.WebSupport.get_data`::

    @app.route('/docs/get_comments')
    def get_comments():
        username = g.user.name if g.user else None
        moderator = g.user.moderator if g.user else False
        node_id = request.args.get('node', '')
        data = support.get_data(node_id, username, moderator)
        return jsonify(**data)

The final function that is needed will call :meth:`~.WebSupport.process_vote`,
and will handle user votes on comments::

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


Comment Moderation
~~~~~~~~~~~~~~~~~~

By default, all comments added through :meth:`~.WebSupport.add_comment` are
automatically displayed.  If you wish to have some form of moderation, you can
pass the `displayed` keyword argument::

   comment = support.add_comment(text, node_id='node_id',
                                 parent_id='parent_id',
                                 username=username, proposal=proposal,
                                 displayed=False)

You can then create a new view to handle the moderation of comments.  It
will be called when a moderator decides a comment should be accepted and
displayed::

   @app.route('/docs/accept_comment', methods=['POST'])
   def accept_comment():
       moderator = g.user.moderator if g.user else False
       comment_id = request.form.get('id')
       support.accept_comment(comment_id, moderator=moderator)
       return 'OK'

Rejecting comments happens via comment deletion.

To perform a custom action (such as emailing a moderator) when a new comment is
added but not displayed, you can pass callable to the :class:`~.WebSupport`
class when instantiating your support object::

   def moderation_callback(comment):
       """Do something..."""

   support = WebSupport(..., moderation_callback=moderation_callback)

The moderation callback must take one argument, which will be the same comment
dict that is returned by :meth:`add_comment`.
