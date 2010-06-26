.. _websupportquickstart:

Web Support Quick Start
=======================

Getting Started
~~~~~~~~~~~~~~~

To use the :ref:`websupportapi` in your application you must import
the :class:`~sphinx.websupport.api.WebSupport` object::

    from sphinx.websupport import support

This provides a reference to a :class:`~sphinx.websupport.api.WebSupport`
object. You will then need to provide some information about your 
environment::

    support.init(srcdir='/path/to/rst/sources/',
                 outdir='/path/to/build/outdir',
		 search='xapian')

Note: You only need to provide a srcdir if you are building documentation.

Building Documentation Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to use the web support package in a webapp, you will need to
build the data it uses. This data includes document data used to display
documentation and search indexes. To build this data, call the build method::

    support.build()

This will create the data the web support package needs and place
it in *outdir*. 

Accessing Document Data
~~~~~~~~~~~~~~~~~~~~~~~

To access document data, call the get_document(docname) method. For example, 
to retrieve the "contents" document, do this::

    contents_doc = support.get_document('contents')

This will return a dictionary containing the context you need to render
a document.

Performing Searches
~~~~~~~~~~~~~~~~~~~

To perform a search, call the get_search_results(q) method, with *q* being
the string to be searched for::

    q = request.GET['q']
    search_doc = support.get_search_results(q)

This will return a dictionary in the same format as get_document() returns.

Full Example
~~~~~~~~~~~~

A more useful example, in the form of a `Flask <http://flask.pocoo.org/>`_
application is::

    from flask import Flask, render_template
    from sphinx.websupport import support

    app = Flask(__name__)

    support.init(outdir='/path/to/sphinx/data')
    
    @app.route('/docs/<path:docname>')
    def doc(docname):
        document = support.get_document(docname)
        return render_template('doc.html', document=document)

    @app.route('/docs/search')
    def search():
        document = support.get_search_results(request.args.get('q', ''))
	return render_template('doc.html', document=document)

In the previous example the doc.html template would look something 
like this::

    {% extends "base.html" %}

    {% block title %}
      {{ document.title }}
    {% endblock %}

    {% block extra_js %}
      <script type="text/javascript" src="/static/jquery.js"></script>
      <script type="text/javascript">
        <!--
        $(document).ready(function() {
          $(".spxcmt").append(' <a href="#" class="sphinx_comment"><img src="/static/comment.png" /></a>');
          $("a.sphinx_comment").click(function() {
            id = $(this).parent().attr('id');
            alert('[ comment stub ' + id + ' ]');
            return false;
          });
        });
        -->
      </script>
    {% endblock %}

    {% block relbar %}
      {{ document.relbar|safe }}
    {% endblock %}

    {% block body %}
      {{ document.body|safe }}
    {% endblock %}

    {% block sidebar %}
      {{ document.sidebar|safe }}
    {% endblock %}

    {% block relbar %}
      {{ document.relbar|safe }}
    {% endblock %}