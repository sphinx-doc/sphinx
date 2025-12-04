.. highlight:: rst

.. _usage-domains:

=======
Domains
=======

.. versionadded:: 1.0

Originally, Sphinx was conceived for a single project, the documentation of the
Python language.  Shortly afterwards, it was made available for everyone as a
documentation tool, but the documentation of Python modules remained deeply
built in -- the most fundamental directives, like ``function``, were designed
for Python objects.  Since Sphinx has become somewhat popular, interest
developed in using it for many different purposes: C/C++ projects, JavaScript,
or even reStructuredText markup (like in this documentation).

While this was always possible, it is now much easier to easily support
documentation of projects using different programming languages or even ones
not supported by the main Sphinx distribution, by providing a **domain** for
every such purpose.

A domain is a collection of markup (reStructuredText :term:`directive`\ s and
:term:`role`\ s) to describe and link to :term:`object`\ s belonging together,
e.g. elements of a programming language.  Directive and role names in a domain
have names like ``domain:name``, e.g. ``py:function``.  Domains can also
provide custom indices (like the Python Module Index).

Having domains means that there are no naming problems when one set of
documentation wants to refer to e.g. C++ and Python classes.  It also means
that extensions that support the documentation of whole new languages are much
easier to write.

This section describes what the domains that are included with Sphinx provide.
The domain API is documented as well, in the section :ref:`domain-api`.

Built-in domains
----------------

The following domains are included within Sphinx:

.. toctree::
   :maxdepth: 1

   standard
   c
   cpp
   javascript
   mathematics
   python
   restructuredtext


Third-party domains
-------------------

Several third-party domains are available as extensions, including:

* `Ada <https://pypi.org/project/sphinxcontrib-adadomain/>`__
* `Antlr4 <https://pypi.org/project/sphinx-syntax/>`__
* `Bazel <https://pypi.org/project/sphinx-bazel/>`__
* `BibTex <https://pypi.org/project/sphinxcontrib-bibtex/>`__
* `Bison/YACC <https://pypi.org/project/sphinx-syntax/>`__
* `Chapel <https://pypi.org/project/sphinxcontrib-chapeldomain/>`__
* `CMake <https://pypi.org/project/sphinxcontrib-moderncmakedomain/>`__
* `Common Lisp <https://pypi.org/project/sphinxcontrib-cldomain/>`__
* `Erlang <https://pypi.org/project/sphinxcontrib-erlangdomain/>`__
* `Fortran <https://pypi.org/project/sphinx-fortran/>`__
* `GraphQL <https://pypi.org/project/graphqldomain/>`__
* `Go <https://pypi.org/project/sphinxcontrib-golangdomain/>`__
* `HTTP <https://pypi.org/project/sphinxcontrib-httpdomain/>`__
* `Hy <https://pypi.org/project/sphinxcontrib-hydomain/>`__
* `Lua <https://pypi.org/project/sphinx-lua-ls/>`__
* `MATLAB <https://pypi.org/project/sphinxcontrib-matlabdomain/>`__
* `PHP <https://pypi.org/project/sphinxcontrib-phpdomain/>`__
* `Ruby <https://pypi.org/project/sphinxcontrib-rubydomain/>`__
* `Rust <https://pypi.org/project/sphinxcontrib-rust/>`__
* `Verilog <https://pypi.org/project/sphinx-verilog-domain/>`__
* `VHDL <https://pypi.org/project/sphinx-vhdl/>`__
* `Visual Basic <https://pypi.org/project/sphinx-vb-domain/>`__

Other domains may be found on the Python Package Index
(via the `Framework :: Sphinx :: Domain`__ classifier),
`GitHub <https://github.com/search?q=sphinx%20domain&type=repositories>`__, or
`GitLab <https://gitlab.com/explore/projects?name=sphinx%20domain>`__.

__ https://pypi.org/search/?c=Framework+%3A%3A+Sphinx+%3A%3A+Domain

.. NOTE: The following all seem unmaintained, last released 2018 or earlier.
         The links are preserved in this comment for reference.

   * `CoffeeScript <https://pypi.org/project/sphinxcontrib-coffee/>`__
   * `DotNET <https://pypi.org/project/sphinxcontrib-dotnetdomain/>`__
   * `dqn <https://pypi.org/project/sphinxcontrib-dqndomain/>`__
   * `Jinja <https://pypi.org/project/sphinxcontrib-jinjadomain/>`__
   * `JSON <https://pypi.org/project/sphinx-jsondomain/>`__
   * `Lasso <https://pypi.org/project/sphinxcontrib-lassodomain/>`__
   * `Operation <https://pypi.org/project/sphinxcontrib-operationdomain/>`__
   * `Scala <https://pypi.org/project/sphinxcontrib-scaladomain/>`__
   * `Lua <https://pypi.org/project/sphinxcontrib-luadomain/>`__


.. _basic-domain-markup:

Basic Markup
------------

Most domains provide a number of :dfn:`object description directives`, used to
describe specific objects provided by modules.  Each directive requires one or
more signatures to provide basic information about what is being described, and
the content should be the description.

A domain will typically keep an internal index of all entities to aid
cross-referencing.
Typically, it will also add entries in the shown general index.
If you want to suppress the addition of an entry in the shown index, you can
give the directive option flag ``:no-index-entry:``.
If you want to exclude the object description from the table of contents, you
can give the directive option flag ``:no-contents-entry:``.
If you want to typeset an object description, without even making it available
for cross-referencing, you can give the directive option flag ``:no-index:``
(which implies ``:no-index-entry:``).
If you do not want to typeset anything, you can give the directive option flag
``:no-typesetting:``.  This can for example be used to create only a target and
index entry for later reference.
Though, note that not every directive in every domain may support these
options.

.. versionadded:: 3.2
   The directive option ``noindexentry`` in the Python, C, C++, and Javascript
   domains.

.. versionadded:: 5.2.3
   The directive option ``:nocontentsentry:`` in the Python, C, C++, Javascript,
   and reStructuredText domains.

.. versionadded:: 7.2
   The directive option ``no-typesetting`` in the Python, C, C++, Javascript,
   and reStructuredText domains.

.. versionchanged:: 7.2

   *  The directive option ``:noindex:`` was renamed
      to ``:no-index:``.
   *  The directive option ``:noindexentry:`` was renamed
      to ``:no-index-entry:``.
   *  The directive option ``:nocontentsentry:`` was renamed
      to ``:no-contents-entry:``.

   The previous names are retained as aliases,
   but will be deprecated and removed
   in a future version of Sphinx.

An example using a Python domain directive::

   .. py:function:: spam(eggs)
                    ham(eggs)

      Spam or ham the foo.

This describes the two Python functions ``spam`` and ``ham``.  (Note that when
signatures become too long, you can break them if you add a backslash to lines
that are continued in the next line.  Example::

   .. py:function:: filterwarnings(action, message='', category=Warning, \
                                   module='', lineno=0, append=False)
      :no-index:

(This example also shows how to use the ``:no-index:`` flag.)

The domains also provide roles that link back to these object descriptions.
For example, to link to one of the functions described in the example above,
you could say ::

   The function :py:func:`spam` does a similar thing.

As you can see, both directive and role names contain the domain name and the
directive name.

The directive option ``:no-typesetting:`` can be used to create a target
(and index entry) which can later be referenced
by the roles provided by the domain.
This is particularly useful for literate programming:

.. code-block:: rst

   .. py:function:: spam(eggs)
      :no-typesetting:

   .. code:: python

      def spam(eggs):
          pass

   The function :py:func:`spam` does nothing.

.. rubric:: Default Domain

For documentation describing objects from solely one domain, authors will not
have to state again its name at each directive, role, etc... after
having specified a default. This can be done either via the config
value :confval:`primary_domain` or via this directive:

.. rst:directive:: .. default-domain:: name

   Select a new default domain.  While the :confval:`primary_domain` selects a
   global default, this only has an effect within the same file.

If no other default is selected, the Python domain (named ``py``) is the
default one, mostly for compatibility with documentation written for older
versions of Sphinx.

Directives and roles that belong to the default domain can be mentioned without
giving the domain name, i.e. ::

   .. function:: pyfunc()

      Describes a Python function.

   Reference to :func:`pyfunc`.

Cross-referencing syntax
~~~~~~~~~~~~~~~~~~~~~~~~

For cross-reference roles provided by domains,
the same :ref:`cross-referencing modifiers <xref-modifiers>` exist
as for general cross-references.
In short:

* You may supply an explicit title and reference target:
  ``:py:mod:`mathematical functions <math>``` will refer to the ``math`` module,
  but the link text will be "mathematical functions".

* If you prefix the content with an exclamation mark (``!``),
  no reference/hyperlink will be created.

* If you prefix the content with ``~``, the link text will only be the last
  component of the target.
  For example, ``:py:meth:`~queue.Queue.get``` will
  refer to ``queue.Queue.get`` but only display ``get`` as the link text.
