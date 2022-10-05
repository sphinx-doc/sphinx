.. _faq:

Sphinx FAQ
==========

This is a list of Frequently Asked Questions about Sphinx.  Feel free to
suggest new entries!

How do I...
-----------

... create PDF files without LaTeX?
   `rinohtype`_ provides a PDF builder that can be used as a drop-in
   replacement for the LaTeX builder.

   .. _rinohtype: https://github.com/brechtm/rinohtype

... get section numbers?
   They are automatic in LaTeX output; for HTML, give a ``:numbered:`` option to
   the :rst:dir:`toctree` directive where you want to start numbering.

... customize the look of the built HTML files?
   Use themes, see :doc:`/usage/theming`.

... add global substitutions or includes?
   Add them in the :confval:`rst_prolog` or :confval:`rst_epilog` config value.

... display the whole TOC tree in the sidebar?
   Use the :data:`toctree` callable in a custom layout template, probably in the
   ``sidebartoc`` block.

... write my own extension?
   See the :doc:`/development/tutorials/index`.

... convert from my existing docs using MoinMoin markup?
   The easiest way is to convert to xhtml, then convert `xhtml to reST`_.
   You'll still need to mark up classes and such, but the headings and code
   examples come through cleanly.

For many more extensions and other contributed stuff, see the sphinx-contrib_
repository.

.. _sphinx-contrib: https://bitbucket.org/birkenfeld/sphinx-contrib/

.. _usingwith:

Using Sphinx with...
--------------------

Read the Docs
    `Read the Docs <https://readthedocs.org>`_ is a documentation hosting
    service based around Sphinx.  They will host sphinx documentation, along
    with supporting a number of other features including version support, PDF
    generation, and more. The `Getting Started`_ guide is a good place to start.

Epydoc
   There's a third-party extension providing an `api role`_ which refers to
   Epydoc's API docs for a given identifier.

Doxygen
   Michael Jones is developing a reST/Sphinx bridge to doxygen called `breathe
   <https://github.com/michaeljones/breathe/tree/master>`_.

SCons
   Glenn Hutchings has written a SCons build script to build Sphinx
   documentation; it is hosted here: https://bitbucket.org/zondo/sphinx-scons

PyPI
   Jannis Leidel wrote a `setuptools command
   <https://pypi.org/project/Sphinx-PyPI-upload/>`_ that automatically
   uploads Sphinx documentation to the PyPI package documentation area at
   https://pythonhosted.org/.

GitHub Pages
   Please add :py:mod:`sphinx.ext.githubpages` to your project.  It allows you
   to publish your document in GitHub Pages.  It generates helper files for
   GitHub Pages on building HTML document automatically.

MediaWiki
   See https://bitbucket.org/kevindunn/sphinx-wiki/wiki/Home, a project by
   Kevin Dunn.

Google Analytics
   You can use a custom ``layout.html`` template, like this:

   .. code-block:: html+jinja

      {% extends "!layout.html" %}

      {%- block extrahead %}
      {{ super() }}
      <script>
        var _gaq = _gaq || [];
        _gaq.push(['_setAccount', 'XXX account number XXX']);
        _gaq.push(['_trackPageview']);
      </script>
      {% endblock %}

      {% block footer %}
      {{ super() }}
      <div class="footer">This page uses <a href="https://analytics.google.com/">
      Google Analytics</a> to collect statistics. You can disable it by blocking
      the JavaScript coming from www.google-analytics.com.
      <script>
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


Google Search
   To replace Sphinx's built-in search function with Google Search, proceed as
   follows:

   1. Go to https://cse.google.com/cse/all to create the Google Search code
      snippet.

   2. Copy the code snippet and paste it into ``_templates/searchbox.html`` in
      your Sphinx project:

      .. code-block:: html+jinja

         <div>
            <h3>{{ _('Quick search') }}</h3>
            <script>
               (function() {
                  var cx = '......';
                  var gcse = document.createElement('script');
                  gcse.async = true;
                  gcse.src = 'https://cse.google.com/cse.js?cx=' + cx;
                  var s = document.getElementsByTagName('script')[0];
                  s.parentNode.insertBefore(gcse, s);
               })();
            </script>
           <gcse:search></gcse:search>
         </div>

   3. Add ``searchbox.html`` to the :confval:`html_sidebars` configuration value.

.. _Getting Started: https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html
.. _api role: https://git.savannah.gnu.org/cgit/kenozooid.git/tree/doc/extapi.py
.. _xhtml to reST: https://docutils.sourceforge.io/sandbox/xhtml2rest/xhtml2rest.py


Sphinx vs. Docutils
-------------------

tl;dr: *docutils* converts reStructuredText to multiple output formats. Sphinx
builds upon docutils to allow construction of cross-referenced and indexed
bodies of documentation.

`docutils`__ is a text processing system for converting plain text
documentation into other, richer formats. As noted in the `docutils
documentation`__, docutils uses *readers* to read a document, *parsers* for
parsing plain text formats into an internal tree representation made up of
different types of *nodes*, and *writers* to output this tree in various
document formats.  docutils provides parsers for one plain text format -
`reStructuredText`__ - though other, *out-of-tree* parsers have been
implemented including Sphinx's :doc:`Markdown parser </usage/markdown>`. On the
other hand, it provides writers for many different formats including HTML,
LaTeX, man pages, Open Document Format and XML.

docutils exposes all of its functionality through a variety of `front-end
tools`__, such as ``rst2html``, ``rst2odt`` and ``rst2xml``. Crucially though,
all of these tools, and docutils itself, are concerned with individual
documents.  They don't support concepts such as cross-referencing, indexing of
documents, or the construction of a document hierarchy (typically manifesting
in a table of contents).

Sphinx builds upon docutils by harnessing docutils' readers and parsers and
providing its own :doc:`/usage/builders/index`. As a result, Sphinx wraps some
of the *writers* provided by docutils. This allows Sphinx to provide many
features that would simply not be possible with docutils, such as those
outlined above.

__ https://docutils.sourceforge.io/
__ https://docutils.sourceforge.io/docs/dev/hacking.html
__ https://docutils.sourceforge.io/rst.html
__ https://docutils.sourceforge.io/docs/user/tools.html


.. _epub-faq:

Epub info
---------

The following list gives some hints for the creation of epub files:

* Split the text into several files. The longer the individual HTML files are,
  the longer it takes the ebook reader to render them.  In extreme cases, the
  rendering can take up to one minute.

* Try to minimize the markup.  This also pays in rendering time.

* For some readers you can use embedded or external fonts using the CSS
  ``@font-face`` directive.  This is *extremely* useful for code listings which
  are often cut at the right margin.  The default Courier font (or variant) is
  quite wide and you can only display up to 60 characters on a line.  If you
  replace it with a narrower font, you can get more characters on a line.  You
  may even use `FontForge <https://fontforge.github.io/>`_ and create
  narrow variants of some free font.  In my case I get up to 70 characters on a
  line.

  You may have to experiment a little until you get reasonable results.

* Test the created epubs. You can use several alternatives.  The ones I am aware
  of are Epubcheck_, Calibre_, FBreader_ (although it does not render the CSS),
  and Bookworm_.  For Bookworm, you can download the source from
  https://code.google.com/archive/p/threepress and run your own local server.

* Large floating divs are not displayed properly.
  If they cover more than one page, the div is only shown on the first page.
  In that case you can copy the :file:`epub.css` from the
  ``sphinx/themes/epub/static/`` directory to your local ``_static/``
  directory and remove the float settings.

* Files that are inserted outside of the ``toctree`` directive must be manually
  included. This sometimes applies to appendixes, e.g. the glossary or
  the indices.  You can add them with the :confval:`epub_post_files` option.

* The handling of the epub cover page differs from the reStructuredText
  procedure which automatically resolves image paths and puts the images
  into the ``_images`` directory.  For the epub cover page put the image in the
  :confval:`html_static_path` directory and reference it with its full path in
  the :confval:`epub_cover` config option.

* kindlegen_ command can convert from epub3 resulting file to ``.mobi`` file
  for Kindle. You can get ``yourdoc.mobi`` under ``_build/epub`` after the
  following command:

  .. code-block:: bash

     $ make epub
     $ kindlegen _build/epub/yourdoc.epub

  The kindlegen command doesn't accept documents that have section
  titles surrounding ``toctree`` directive:

  .. code-block:: rst

     Section Title
     =============

     .. toctree::

        subdocument

     Section After Toc Tree
     ======================

  kindlegen assumes all documents order in line, but the resulting document
  has complicated order for kindlegen::

     ``parent.xhtml`` -> ``child.xhtml`` -> ``parent.xhtml``

  If you get the following error, fix your document structure:

  .. code-block:: none

     Error(prcgen):E24011: TOC section scope is not included in the parent chapter:(title)
     Error(prcgen):E24001: The table of content could not be built.

.. _Epubcheck: https://github.com/IDPF/epubcheck
.. _Calibre: https://calibre-ebook.com/
.. _FBreader: https://fbreader.org/
.. _Bookworm: https://www.oreilly.com/bookworm/index.html
.. _kindlegen: https://www.amazon.com/gp/feature.html?docId=1000765211

.. _texinfo-faq:

Texinfo info
------------

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
``*note:`` with ``see`` and hide the ``target-id``.  For example:

    :ref:`texinfo-links`

One can disable generation of the inline references in a document
with :confval:`texinfo_cross_references`.  That makes
an info file more readable with stand-alone reader (``info``).

The exact behavior of how Emacs displays references is dependent on the variable
``Info-hide-note-references``.  If set to the value of ``hide``, Emacs will hide
both the ``*note:`` part and the ``target-id``.  This is generally the best way
to view Sphinx-based documents since they often make frequent use of links and
do not take this limitation into account.  However, changing this variable
affects how all Info documents are displayed and most do take this behavior
into account.

If you want Emacs to display Info files produced by Sphinx using the value
``hide`` for ``Info-hide-note-references`` and the default value for all other
Info files, try adding the following Emacs Lisp code to your start-up file,
``~/.emacs.d/init.el``.

.. code-block:: elisp

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

- Links to external Info files can be created using the somewhat official URI
  scheme ``info``.  For example::

     info:Texinfo#makeinfo_options
