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

... display the whole TOC tree in the sidebar?
   Use the :data:`toctree` callable in a custom layout template, probably in the
   ``sidebartoc`` block.

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

PyPI
   Jannis Leidel wrote a `setuptools command
   <http://pypi.python.org/pypi/Sphinx-PyPI-upload>`_ that automatically uploads
   Sphinx documentation to the PyPI package documentation area at
   http://packages.python.org/.

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


.. _epub-faq:

Epub info
---------

The epub builder is currently in an experimental stage.  It has only been tested
with the Sphinx documentation itself.  If you want to create epubs, here are
some notes:

* Split the text into several files. The longer the individual HTML files are,
  the longer it takes the ebook reader to render them.  In extreme cases, the
  rendering can take up to one minute.

* Try to minimize the markup.  This also pays in rendering time.

* For some readers you can use embedded or external fonts using the CSS
  ``@font-face`` directive.  This is *extremely* useful for code listings which
  are often cut at the right margin.  The default Courier font (or variant) is
  quite wide and you can only display up to 60 characters on a line.  If you
  replace it with a narrower font, you can get more characters on a line.  You
  may even use `FontForge <http://fontforge.sourceforge.net/>`_ and create
  narrow variants of some free font.  In my case I get up to 70 characters on a
  line.

  You may have to experiment a little until you get reasonable results.

* Test the created epubs. You can use several alternatives.  The ones I am aware
  of are Epubcheck_, Calibre_, FBreader_ (although it does not render the CSS),
  and Bookworm_.  For bookworm you can download the source from
  http://code.google.com/p/threepress/ and run your own local server.

.. _Epubcheck: http://code.google.com/p/epubcheck/
.. _Calibre: http://calibre-ebook.com/
.. _FBreader: http://www.fbreader.org/
.. _Bookworm: http://bookworm.oreilly.com/
