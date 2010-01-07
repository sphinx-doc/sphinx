.. _faq:

Sphinx FAQ
==========

This is a list of Frequently Asked Questions about Sphinx.  Feel free to
suggest new entries!

How do I...
-----------

... create PDF files without LaTeX?
   You can use `rst2pdf <http://rst2pdf.googlecode.com>`_ version 0.12 or greater
   which comes with built-in Sphinx integration.  See the :ref:`builders`
   section for details.

... get section numbers?
   They are automatic in LaTeX output; for HTML, give a ``:numbered:`` option to
   the :dir:`toctree` directive where you want to start numbering.

... customize the look of the built HTML files?
   Use themes, see :doc:`theming`.

... add global substitutions or includes?
   Add them in the :confval:`rst_epilog` config value.

... write my own extension?
   See the :ref:`extension tutorial <exttut>`.

... convert from my existing docs using MoinMoin markup?
   The easiest way is to convert to xhtml, then convert `xhtml to reST`_.  You'll
   still need to mark up classes and such, but the headings and code examples
   come through cleanly.


Using Sphinx with...
--------------------

Epydoc
   There's a third-party extension providing an `api role`_ which refers to
   Epydoc's API docs for a given identifier.

Doxygen
   Michael Jones is developing a reST/Sphinx bridge to doxygen called `breathe
   <http://github.com/michaeljones/breathe/tree/master>`_.

SCons
   Glenn Hutchings has written a SCons build script to build Sphinx
   documentation; it is hosted here: http://bitbucket.org/zondo/sphinx-scons

github pages
   You can use `Michael Jones' sphinx-to-github tool
   <http://github.com/michaeljones/sphinx-to-github/tree/master>`_ to prepare
   Sphinx HTML output.

Google Analytics
   You can use a custom ``layout.html`` template, like this:

   .. code-block:: html+django

      {% extends "!layout.html" %}

      {%- block extrahead %}
      {{ super() }}
      <script type="text/javascript">
        var _gaq = _gaq || [];
        _gaq.push(['_setAccount', 'XXX account number XXX']);
        _gaq.push(['_trackPageview']);
      </script>
      {% endblock %}

      {% block footer %}
      {{ super() }}
      <div class="footer">This page uses <a href="http://analytics.google.com/">
      Google Analytics</a> to collect statistics. You can disable it by blocking
      the JavaScript coming from www.google-analytics.com.
      <script type="text/javascript">
        (function() {
          var ga = document.createElement('script');
          ga.src = ('https:' == document.location.protocol ?
                    'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
          ga.setAttribute('async', 'true');
          document.documentElement.firstChild.appendChild(ga);
        })();
      </script>
      </div>
      {% endblock %}


.. _api role: http://git.savannah.gnu.org/cgit/kenozooid.git/tree/doc/extapi.py
.. _xhtml to reST: http://docutils.sourceforge.net/sandbox/xhtml2rest/xhtml2rest.py
