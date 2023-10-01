.. highlight:: rst

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


.. _basic-domain-markup:

Basic Markup
------------

Most domains provide a number of :dfn:`object description directives`, used to
describe specific objects provided by modules.  Each directive requires one or
more signatures to provide basic information about what is being described, and
the content should be the description.

A domain will typically keep an internal index of all entities to aid
cross-referencing.
Typically it will also add entries in the shown general index.
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

   .. code::

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

For cross-reference roles provided by domains, the same facilities exist as for
general cross-references.  See :ref:`xref-syntax`.

In short:

* You may supply an explicit title and reference target: ``:role:`title
  <target>``` will refer to *target*, but the link text will be *title*.

* If you prefix the content with ``!``, no reference/hyperlink will be created.

* If you prefix the content with ``~``, the link text will only be the last
  component of the target.  For example, ``:py:meth:`~Queue.Queue.get``` will
  refer to ``Queue.Queue.get`` but only display ``get`` as the link text.


The JavaScript Domain
---------------------

The JavaScript domain (name **js**) provides the following directives:

.. rst:directive:: .. js:module:: name

   This directive sets the module name for object declarations that follow
   after. The module name is used in the global module index and in cross
   references. This directive does not create an object heading like
   :rst:dir:`py:class` would, for example.

   By default, this directive will create a linkable entity and will cause an
   entry in the global module index, unless the ``no-index`` option is
   specified.  If this option is specified, the directive will only update the
   current module name.

   .. versionadded:: 1.6
   .. versionchanged:: 5.2

      Module directives support body content.

.. rst:directive:: .. js:function:: name(signature)

   Describes a JavaScript function or method.  If you want to describe
   arguments as optional use square brackets as :ref:`documented <signatures>`
   for Python signatures.

   You can use fields to give more details about arguments and their expected
   types, errors which may be thrown by the function, and the value being
   returned::

      .. js:function:: $.getJSON(href, callback[, errback])

         :param string href: An URI to the location of the resource.
         :param callback: Gets called with the object.
         :param errback:
             Gets called in case the request fails. And a lot of other
             text so we need multiple lines.
         :throws SomeError: For whatever reason in that case.
         :returns: Something.

   This is rendered as:

   .. js:function:: $.getJSON(href, callback[, errback])
      :no-index:

      :param string href: An URI to the location of the resource.
      :param callback: Gets called with the object.
      :param errback:
          Gets called in case the request fails. And a lot of other
          text so we need multiple lines.
      :throws SomeError: For whatever reason in that case.
      :returns: Something.

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`javascript_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

.. rst:directive:: .. js:method:: name(signature)

   This directive is an alias for :rst:dir:`js:function`, however it describes
   a function that is implemented as a method on a class object.

   .. versionadded:: 1.6

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`javascript_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

.. rst:directive:: .. js:class:: name

   Describes a constructor that creates an object.  This is basically like a
   function but will show up with a `class` prefix::

      .. js:class:: MyAnimal(name[, age])

         :param string name: The name of the animal
         :param number age: an optional age for the animal

   This is rendered as:

   .. js:class:: MyAnimal(name[, age])
      :no-index:

      :param string name: The name of the animal
      :param number age: an optional age for the animal

   .. rst:directive:option:: single-line-parameter-list
      :type: no value

      Ensures that the function's parameters will be emitted on a single logical
      line, overriding :confval:`javascript_maximum_signature_line_length` and
      :confval:`maximum_signature_line_length`.

      .. versionadded:: 7.1

.. rst:directive:: .. js:data:: name

   Describes a global variable or constant.

.. rst:directive:: .. js:attribute:: object.name

   Describes the attribute *name* of *object*.

.. _js-roles:

These roles are provided to refer to the described objects:

.. rst:role:: js:mod
          js:func
          js:meth
          js:class
          js:data
          js:attr


The reStructuredText domain
---------------------------

The reStructuredText domain (name **rst**) provides the following directives:

.. rst:directive:: .. rst:directive:: name

   Describes a reST directive.  The *name* can be a single directive name or
   actual directive syntax (`..` prefix and `::` suffix) with arguments that
   will be rendered differently.  For example::

      .. rst:directive:: foo

         Foo description.

      .. rst:directive:: .. bar:: baz

         Bar description.

   will be rendered as:

   .. rst:directive:: foo
      :no-index:

      Foo description.

   .. rst:directive:: .. bar:: baz
      :no-index:

      Bar description.

.. rst:directive:: .. rst:directive:option:: name

   Describes an option for reST directive.  The *name* can be a single option
   name or option name with arguments which separated with colon (``:``).
   For example::

       .. rst:directive:: toctree

          .. rst:directive:option:: caption: caption of ToC

          .. rst:directive:option:: glob

   will be rendered as:

   .. rst:directive:: toctree
      :no-index:

      .. rst:directive:option:: caption: caption of ToC
         :no-index:

      .. rst:directive:option:: glob
         :no-index:

   .. rubric:: options

   .. rst:directive:option:: type: description of argument
      :type: text

      Describe the type of option value.

      For example::

         .. rst:directive:: toctree

            .. rst:directive:option:: maxdepth
               :type: integer or no value

      .. versionadded:: 2.1

.. rst:directive:: .. rst:role:: name

   Describes a reST role.  For example::

      .. rst:role:: foo

         Foo description.

   will be rendered as:

   .. rst:role:: foo
      :no-index:

      Foo description.

.. _rst-roles:

These roles are provided to refer to the described objects:

.. rst:role:: rst:dir
              rst:role

.. _math-domain:

The Math Domain
---------------

The math domain (name **math**) provides the following roles:

.. rst:role:: math:numref

   Role for cross-referencing equations defined by :rst:dir:`math` directive
   via their label.  Example::

      .. math:: e^{i\pi} + 1 = 0
         :label: euler

      Euler's identity, equation :math:numref:`euler`, was elected one of the
      most beautiful mathematical formulas.

   .. versionadded:: 1.8

More domains
------------

The sphinx-contrib_ repository contains more domains available as extensions;
currently Ada_, CoffeeScript_, Erlang_, HTTP_, Lasso_, MATLAB_, PHP_, and Ruby_
domains. Also available are domains for `Chapel`_, `Common Lisp`_, dqn_, Go_,
Jinja_, Operation_, and Scala_.

.. _sphinx-contrib: https://github.com/sphinx-contrib

.. _Ada: https://pypi.org/project/sphinxcontrib-adadomain/
.. _Chapel: https://pypi.org/project/sphinxcontrib-chapeldomain/
.. _CoffeeScript: https://pypi.org/project/sphinxcontrib-coffee/
.. _Common Lisp: https://pypi.org/project/sphinxcontrib-cldomain/
.. _dqn: https://pypi.org/project/sphinxcontrib-dqndomain/
.. _Erlang: https://pypi.org/project/sphinxcontrib-erlangdomain/
.. _Go: https://pypi.org/project/sphinxcontrib-golangdomain/
.. _HTTP: https://pypi.org/project/sphinxcontrib-httpdomain/
.. _Jinja: https://pypi.org/project/sphinxcontrib-jinjadomain/
.. _Lasso: https://pypi.org/project/sphinxcontrib-lassodomain/
.. _MATLAB: https://pypi.org/project/sphinxcontrib-matlabdomain/
.. _Operation: https://pypi.org/project/sphinxcontrib-operationdomain/
.. _PHP: https://pypi.org/project/sphinxcontrib-phpdomain/
.. _Ruby: https://github.com/sphinx-contrib/rubydomain
.. _Scala: https://pypi.org/project/sphinxcontrib-scaladomain/
