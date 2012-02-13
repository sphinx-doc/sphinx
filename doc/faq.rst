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
   the :rst:dir:`toctree` directive where you want to start numbering.

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


.. _usingwith:

Using Sphinx with...
--------------------

Read the Docs
    http://readthedocs.org is a documentation hosting service based around Sphinx.
    They will host sphinx documentation, along with supporting a number of other
    features including version support, PDF generation, and more. The `Getting
    Started <http://read-the-docs.readthedocs.org/en/latest/getting_started.html>`_
    guide is a good place to start.

Epydoc
   There's a third-party extension providing an `api role`_ which refers to
   Epydoc's API docs for a given identifier.

Doxygen
   Michael Jones is developing a reST/Sphinx bridge to doxygen called `breathe
   <http://github.com/michaeljones/breathe/tree/master>`_.

SCons
   Glenn Hutchings has written a SCons build script to build Sphinx
   documentation; it is hosted here: https://bitbucket.org/zondo/sphinx-scons

PyPI
   Jannis Leidel wrote a `setuptools command
   <http://pypi.python.org/pypi/Sphinx-PyPI-upload>`_ that automatically uploads
   Sphinx documentation to the PyPI package documentation area at
   http://packages.python.org/.

GitHub Pages
   Directories starting with underscores are ignored by default which breaks
   static files in Sphinx.  GitHub's preprocessor can be `disabled
   <https://github.com/blog/572-bypassing-jekyll-on-github-pages>`_ to support
   Sphinx HTML output properly.

MediaWiki
   See https://bitbucket.org/kevindunn/sphinx-wiki, a project by Kevin Dunn.

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

* Large floating divs are not displayed properly.
  If they cover more than one page, the div is only shown on the first page.
  In that case you can copy the :file:`epub.css` from the
  ``sphinx/themes/epub/static/`` directory to your local ``_static/``
  directory and remove the float settings.

* Files that are inserted outside of the ``toctree`` directive must be manually
  included. This sometimes applies to appendixes, e.g. the glossary or
  the indices.  You can add them with the :confval:`epub_post_files` option.

.. _Epubcheck: http://code.google.com/p/epubcheck/
.. _Calibre: http://calibre-ebook.com/
.. _FBreader: http://www.fbreader.org/
.. _Bookworm: http://bookworm.oreilly.com/


.. _texinfo-faq:

Texinfo info
------------

The Texinfo builder is currently in an experimental stage but has successfully
been used to build the documentation for both Sphinx and Python.  The intended
use of this builder is to generate Texinfo that is then processed into Info
files.

There are two main programs for reading Info files, ``info`` and GNU Emacs.  The
``info`` program has less features but is available in most Unix environments
and can be quickly accessed from the terminal.  Emacs provides better font and
color display and supports extensive customization (of course).


.. _texinfo-links:

Displaying Links
~~~~~~~~~~~~~~~~

One noticeable problem you may encounter with the generated Info files is how
references are displayed.  If you read the source of an Info file, a reference
to this section would look like::

    * note Displaying Links: target-id

In the stand-alone reader, ``info``, references are displayed just as they
appear in the source.  Emacs, on the other-hand, will by default replace
``\*note:`` with ``see`` and hide the ``target-id``.  For example:

    :ref:`texinfo-links`

The exact behavior of how Emacs displays references is dependent on the variable
``Info-hide-note-references``.  If set to the value of ``hide``, Emacs will hide
both the ``\*note:`` part and the ``target-id``.  This is generally the best way
to view Sphinx-based documents since they often make frequent use of links and
do not take this limitation into account.  However, changing this variable
affects how all Info documents are displayed and most due take this behavior
into account.

If you want Emacs to display Info files produced by Sphinx using the value
``hide`` for ``Info-hide-note-references`` and the default value for all other
Info files, try adding the following Emacs Lisp code to your start-up file,
``~/.emacs.d/init.el``.

::

   (defadvice info-insert-file-contents (after
                                         sphinx-info-insert-file-contents
                                         activate)
     "Hack to make `Info-hide-note-references' buffer-local and
   automatically set to `hide' iff it can be determined that this file
   was created from a Texinfo file generated by Docutils or Sphinx."
     (set (make-local-variable 'Info-hide-note-references)
          (default-value 'Info-hide-note-references))
     (save-excursion
       (save-restriction
         (widen) (goto-char (point-min))
         (when (re-search-forward
                "^Generated by \\(Sphinx\\|Docutils\\)"
                (save-excursion (search-forward "\x1f" nil t)) t)
           (set (make-local-variable 'Info-hide-note-references)
                'hide)))))


Notes
~~~~~

The following notes may be helpful if you want to create Texinfo files:

- Each section corresponds to a different ``node`` in the Info file.

- Colons (``:``) cannot be properly escaped in menu entries and xrefs.
  They will be replaced with semicolons (``;``).

- In the HTML and Tex output, the word ``see`` is automatically inserted before
  all xrefs.

- Links to external Info files can be created using the somewhat official URI
  scheme ``info``.  For example::

     info:Texinfo#makeinfo_options

  which produces:

     info:Texinfo#makeinfo_options

- Inline markup appears as follows in Info:

  * strong -- \*strong\*
  * emphasis -- _emphasis_
  * literal -- \`literal'

  It is possible to change this behavior using the Texinfo command
  ``@definfoenclose``.  For example, to make inline markup more closely resemble
  reST, add the following to your :file:`conf.py`::

     texinfo_elements = {'preamble': """\
     @definfoenclose strong,**,**
     @definfoenclose emph,*,*
     @definfoenclose code,`@w{}`,`@w{}`
     """}
