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
it in *outdir*. You can then access 
:class:`~sphinx.websupport.document.Document` objects by calling
the get_document(docname) method. For example, to retrieve the "contents" 
document, do this::

    contents_doc = support.get_document('contents')

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

This simple application will return a 
:class:`~sphinx.websupport.document.Document` object corresponding 
to the *docname* variable. This object will have *title* attribute,
as well as a list of HTML "slices". Each slice contains some HTML,
and when joined they form the body of a Sphinx document. Each slice
may or may not be commentable. If a slice is commentable, it will
have an *id* attribute which is used to associate a comment with
part of a document.

In the previous example the doc.html template would look something 
like this::

    {% extends "base.html" %}

    {% block title %}
      {{ document.title }}
    {% endblock %}

    {% block body %}
      {% for slice in document.slices -%}
        {{ slice.html|safe }}
        {% if slice.commentable -%}
          <a href="#" onclick="alert('[ comment stub for <{{ slice.id }}> ]'); return false;">
            comment
          </a>
        {%- endif %}
      {%- endfor %}
    {% endblock %}
