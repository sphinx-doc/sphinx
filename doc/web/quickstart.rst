.. _websupportquickstart:

Web Support Quick Start
=======================

To use the :ref:`websupportapi` in your application you must import
the :class:`~sphinx.websupport.api.WebSupport` object::

    from sphinx.websupport import support

This provides a reference to a :class:`~sphinx.websupport.api.WebSupport`
object. You will then need to provide some information about your 
environment::

    support.init(srcdir='/path/to/rst/sources/',
                 outdir='/path/to/build/outdir')

You only need to provide a srcdir if you are building documentation::

    support.build()

This will create the data the web support package needs and place
it in *outdir*. You can then access this data by calling the 
get_document(docname) method. For example, to retrieve the "contents" 
document, do this::

    contents_doc = support.get_document('contents')

This will return a dictionary containing the context you need to render
a document.

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

    {% block body %}
      {{ document.body|safe }}
    {% endblock %}

    {% block sidebar %}
    {% endblock %}
