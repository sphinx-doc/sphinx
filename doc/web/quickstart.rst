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
documents.

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

This dict can then be used as context for templates. The goal is to be
easy to integrate with your existing templating system. An example using 
`Jinja2 <http://jinja.pocoo.org/2/>`_ is:

.. sourcecode:: html+jinja

    {%- extends "layout.html" %}

    {%- block title %}
      {{ document.title }}
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

Most likely you'll want to create one function that can handle all of
document requests. An example `Flask <http://flask.pocoo.org/>`_ function
that performs this is::

    @app.route('/<path:docname>')
    def doc(docname):
        document = support.get_document(docname)
        return render_template('doc.html', document=document)

This captures the request path, and passes it directly to 
:meth:`~sphinx.websupport.WebSupport.get_document`, which then retrieves
the correct document.

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

The web support package provides a way to attach comments to some nodes
in your document. It marks these nodes by adding a class and id to these
nodes. A client side script can then locate these nodes, and manipulate
them to allow commenting. A `jQuery <http://jquery.com>`_ script is also 
being developed that will be included when it's complete. For now you can 
find the script here: `websupport.js <http://bit.ly/cyaRaF>`_. This script 
will use AJAX for all communications with the server. You can create your 
own script for the front end if this doesn't meet your needs. More 
information on that can be found :ref:`here <websupportfrontend>`.

Before loading this script in your page, you need to create a COMMENT_OPTIONS
object describing how the script should function. In the simplest case you
will just need tell the script whether the current user is allowed to vote.
Once this is done you can import the script as you would any other:

.. sourcecode:: guess

    <script type="text/javascript">
      var COMMENT_OPTIONS =  {
        {%- if g.user %}
	  voting: true,
	{%- endif %}
      }
    </script>
    <script type="text/javascript" src="/static/websupport.js></script>

You will then need to define some templates that the script uses to 
display comments. The first template defines the layout for the popup 
div used to display comments:

.. sourcecode:: guess

   <script type="text/html" id="popup_template">
     <div class="popup_comment">
       <a id="comment_close" href="#">x</a>
       <h1>Comments</h1>
       <form method="post" id="comment_form" action="/docs/add_comment">
 	 <textarea name="comment"></textarea>
	 <input type="submit" value="add comment" id="comment_button" />
	 <input type="hidden" name="parent" />
       <p class="sort_options">
	 Sort by: 
	 <a href="#" class="sort_option" id="rating">top</a>
	 <a href="#" class="sort_option" id="ascage">newest</a>
	 <a href="#" class="sort_option" id="age">oldest</a>
       </p>
       </form>
       <h3 id="comment_notification">loading comments... <img src="/static/ajax-loader.gif" alt="" /></h3>
       <ul id="comment_ul"></ul>
     </div>
     <div id="focuser"></div>
   </script> 

The next template is an `li` that contains the form used to 
reply to a comment:

.. sourcecode:: guess

   <script type="text/html" id="reply_template">
     <li>
       <div class="reply_div" id="rd<%id%>">
	 <form id="rf<%id%>">
	   <textarea name="comment"></textarea>
           <input type="submit" value="add reply" />
           <input type="hidden" name="parent" value="c<%id%>" />
         </form>
       </div>
     </li>
   </script>

The final template contains HTML that will be used to display comments
in the comment tree:

.. sourcecode:: guess

   <script type="text/html" id="comment_template">
     <div  id="cd<%id%>" class="spxcdiv">
       <div class="vote">
	 <div class="arrow">
	   <a href="#" id="uv<%id%>" class="vote">
	     <img src="<%upArrow%>" />
	   </a>
	   <a href="#" id="uu<%id%>" class="un vote">
	     <img src="<%upArrowPressed%>" />
	   </a>
	 </div>
	 <div class="arrow">
	   <a href="#" id="dv<%id%>" class="vote">
	     <img src="<%downArrow%>" id="da<%id%>" />
	   </a>
	   <a href="#" id="du<%id%>" class="un vote">
	     <img src="<%downArrowPressed%>" />
	   </a>
	 </div>
       </div>
       <div class="comment_content">
	 <p class="tagline comment">
	   <span class="user_id"><%username%></span>
	   <span class="rating"><%pretty_rating%></span>
	   <span class="delta"><%time.delta%></span>
	 </p>
	 <p class="comment_text comment"><%text%></p>
	 <p class="comment_opts comment">
	   <a href="#" class="reply" id="rl<%id%>">reply</a>
	   <a href="#" class="close_reply" id="cr<%id%>">hide</a>
	 </p>
	 <ul class="children" id="cl<%id%>"></ul>
       </div>
       <div class="clearleft"></div>
     </div>
   </script>

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
and is aptly named :meth:`~sphinx.websupport.WebSupport.get_comments`::

    @app.route('/docs/get_comments')
    def get_comments():
        user_id = g.user.id if g.user else None
        parent_id = request.args.get('parent', '')
        comments = support.get_comments(parent_id, user_id)
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
