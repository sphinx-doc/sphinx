.. _websupportquickstart:

Web Support Quick Start
=======================

Building Documentation Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make use of the web support package in your application you'll
need to build that data it uses. This data includes pickle files representing
documents, search indices, and node data that is used to track where
comments and other things are in a document. To do this you will need
to create an instance of the :class:`~sphinx.websupport.api.WebSupport` 
class and call it's :meth:`~sphinx.websupport.WebSupport.build` method::

    from sphinx.websupport import WebSupport

    support = WebSupport(srcdir='/path/to/rst/sources/',
                         outdir='/path/to/build/outdir',
		         search='xapian')

    support.build()

This will read reStructuredText sources from `srcdir` and place the
necessary data in `outdir`. This directory contains all the data needed
to display documents, search through documents, and add comments to
documents. It will also contain a subdirectory named "static", which
contains static files. These files will be linked to by Sphinx documents,
and should be served from "/static".

.. note::

    If you wish to serve static files from a path other than "/static", you
    can do so by providing the *staticdir* keyword argument when creating
    the :class:`~sphinx.websupport.api.WebSupport` object.

Integrating Sphinx Documents Into Your Webapp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that you have the data, it's time to do something useful with it.
Start off by creating a :class:`~sphinx.websupport.WebSupport` object
for your application::
    
    from sphinx.websupport import WebSupport

    support = WebSupport(datadir='/path/to/the/data',
                         search='xapian')

You'll only need one of these for each set of documentation you will be
working with. You can then call it's 
:meth:`~sphinx.websupport.WebSupport.get_document` method to access
individual documents::

    contents = support.get_document('contents')

This will return a dictionary containing the following items:

* **body**: The main body of the document as HTML
* **sidebar**: The sidebar of the document as HTML  
* **relbar**: A div containing links to related documents
* **title**: The title of the document
* **DOCUMENTATION_OPTIONS**: Javascript containing documentation options
* **COMMENT_OPTIONS**: Javascript containing comment options

This dict can then be used as context for templates. The goal is to be
easy to integrate with your existing templating system. An example using 
`Jinja2 <http://jinja.pocoo.org/2/>`_ is:

.. sourcecode:: html+jinja

    {%- extends "layout.html" %}

    {%- block title %}
      {{ document.title }}
    {%- endblock %}

    {%- block js %}
      <script type="text/javascript">
        {{ document.DOCUMENTATION_OPTIONS|safe }}
	{{ document.COMMENT_OPTIONS|safe }}
      </script>
      {{ super() }}
      <script type="text/javascript" src="/static/websupport.js"></script>
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

To use certain features such as voting it must be possible to authenticate
users. The details of the authentication are left to the your application.
Once a user has been authenticated you can pass the user's details to certain
:class:`~sphinx.websupport.WebSupport` methods using the *username* and
*moderator* keyword arguments. The web support package will store the
username with comments and votes. The only caveat is that if you allow users
to change their username, you must update the websupport package's data::

   support.update_username(old_username, new_username)

*username* should be a unique string which identifies a user, and *moderator*
should be a boolean representing whether the user has moderation
privilieges. The default value for *moderator* is *False*.

An example `Flask <http://flask.pocoo.org/>`_ function that checks whether
a user is logged in, and the retrieves a document is::

    @app.route('/<path:docname>')
    def doc(docname):
        if g.user:
	    document = support.get_document(docname, g.user.name,
	                                    g.user.moderator)
	else:
	    document = support.get_document(docname)
        return render_template('doc.html', document=document)

The first thing to notice is that the *docname* is just the request path.
If the user is authenticated then the username and moderation status are
passed along with the docname to 
:meth:`~sphinx.websupport.WebSupport.get_document`. The web support package
will then add this data to the COMMENT_OPTIONS that are used in the template.

.. note::

   This only works works if your documentation is served from your
   document root. If it is served from another directory, you will
   need to prefix the url route with that directory::

       @app.route('/docs/<path:docname>')

Performing Searches
~~~~~~~~~~~~~~~~~~~

To use the search form built-in to the Sphinx sidebar, create a function
to handle requests to the url 'search' relative to the documentation root.
The user's search query will be in the GET parameters, with the key `q`.
Then use the :meth:`~sphinx.websupport.WebSupport.get_search_results` method
to retrieve search results. In `Flask <http://flask.pocoo.org/>`_ that 
would be like this::

    @app.route('/search')
    def search():
        q = request.args.get('q')
        document = support.get_search_results(q)
        return render_template('doc.html', document=document)

Note that we used the same template to render our search results as we
did to render our documents. That's because 
:meth:`~sphinx.websupport.WebSupport.get_search_results` returns a context
dict in the same format that
:meth:`~sphinx.websupport.WebSupport.get_document` does.

Comments
~~~~~~~~

Now that this is done it's time to define the functions that handle
the AJAX calls from the script. You will need three functions. The first
function is used to add a new comment, and will call the web support method
:meth:`~sphinx.websupport.WebSupport.add_comment`::

    @app.route('/docs/add_comment', methods=['POST'])
    def add_comment():
        parent_id = request.form.get('parent', '')
        text = request.form.get('text', '')
        username = g.user.name if g.user is not None else 'Anonymous'
        comment = support.add_comment(parent_id, text, username=username)
        return jsonify(comment=comment)

Then next function handles the retrieval of comments for a specific node, 
and is aptly named :meth:`~sphinx.websupport.WebSupport.get_data`::

    @app.route('/docs/get_comments')
    def get_comments():
        user_id = g.user.id if g.user else None
        parent_id = request.args.get('parent', '')
        comments = support.get_data(parent_id, user_id)
        return jsonify(comments=comments)

The final function that is needed will call
:meth:`~sphinx.websupport.WebSupport.process_vote`, and will handle user
votes on comments::

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

.. note::

   Authentication is left up to your existing web application. If you do
   not have an existing authentication system there are many readily 
   available for different frameworks. The web support system stores only
   the user's unique integer `user_id` and uses this both for storing votes 
   and retrieving vote information. It is up to you to ensure that the 
   user_id passed in is unique, and that the user is authenticated. The 
   default backend will only allow one vote per comment per `user_id`.
