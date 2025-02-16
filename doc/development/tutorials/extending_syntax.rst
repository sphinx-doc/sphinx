.. _tutorial-extending-syntax:

Extending syntax with roles and directives
==========================================

Overview
--------

The syntax of both reStructuredText and MyST can be extended
by creating new **directives** - for block-level elements -
and **roles** - for inline elements.

In this tutorial we shall extend Sphinx to add:

* A ``hello`` role, that will simply output the text ``Hello {text}!``.
* A ``hello`` directive, that will simply output the text ``Hello {text}!``,
  as a paragraph.

For this extension, you will need some basic understanding of Python,
and we shall also introduce aspects of the docutils_ API.

Setting up the project
----------------------

You can either use an existing Sphinx project
or create a new one using :program:`sphinx-quickstart`.

With this we will add the extension to the project,
within the :file:`source` folder:

#. Create an :file:`_ext` folder in :file:`source`
#. Create a new Python file in the :file:`_ext` folder called
   :file:`helloworld.py`

Here is an example of the folder structure you might obtain:

.. code-block:: text

      └── source
          ├── _ext
          │   └── helloworld.py
          ├── conf.py
          ├── index.rst


Writing the extension
---------------------

Open :file:`helloworld.py` and paste the following code in it:

.. literalinclude:: examples/helloworld.py
   :language: python
   :linenos:

Some essential things are happening in this example:

The role class
...............

Our new role is declared in the ``HelloRole`` class.

.. literalinclude:: examples/helloworld.py
   :language: python
   :linenos:
   :pyobject: HelloRole

This class extends the :class:`.SphinxRole` class.
The class contains a ``run`` method,
which is a requirement for every role.
It contains the main logic of the role and it
returns a tuple containing:

- a list of inline-level docutils nodes to be processed by Sphinx.
- an (optional) list of system message nodes

The directive class
...................

Our new directive is declared in the ``HelloDirective`` class.

.. literalinclude:: examples/helloworld.py
   :language: python
   :linenos:
   :pyobject: HelloDirective

This class extends the :class:`.SphinxDirective` class.
The class contains a ``run`` method,
which is a requirement for every directive.
It contains the main logic of the directive and it
returns a list of block-level docutils nodes to be processed by Sphinx.
It also contains a ``required_arguments`` attribute,
which tells Sphinx how many arguments are required for the directive.

What are docutils nodes?
........................

When Sphinx parses a document,
it creates an "Abstract Syntax Tree" (AST) of nodes
that represent the content of the document in a structured way,
that is generally independent of any one
input (rST, MyST, etc) or output (HTML, LaTeX, etc) format.
It is a tree because each node can have children nodes, and so on:

.. code-block:: xml

      <document>
         <paragraph>
            <text>
               Hello world!

The docutils_ package provides many `built-in nodes <docutils nodes_>`_,
to represent different types of content such as
text, paragraphs, references, tables, etc.

Each node type generally only accepts a specific set of direct child nodes,
for example the ``document`` node should only contain "block-level" nodes,
such as ``paragraph``, ``section``, ``table``, etc,
whilst the ``paragraph`` node should only contain "inline-level" nodes,
such as ``text``, ``emphasis``, ``strong``, etc.

.. seealso::

   The docutils documentation on
   `creating directives <docutils directives_>`_, and
   `creating roles <docutils roles_>`_.

The ``setup`` function
......................

This function is a requirement.
We use it to plug our new directive into Sphinx.

.. literalinclude:: examples/helloworld.py
   :language: python
   :pyobject: setup

The simplest thing you can do is to call the
:meth:`.Sphinx.add_role` and :meth:`.Sphinx.add_directive` methods,
which is what we've done here.
For this particular call, the first argument is the name of the role/directive itself
as used in a reStructuredText file.
In this case, we would use ``hello``. For example:

.. code-block:: rst

   Some intro text here...

   .. hello:: world

   Some text with a :hello:`world` role.

We also return the :ref:`extension metadata <ext-metadata>` that indicates the
version of our extension, along with the fact that it is safe to use the
extension for both parallel reading and writing.

Using the extension
-------------------

The extension has to be declared in your :file:`conf.py` file to make Sphinx
aware of it. There are two steps necessary here:

#. Add the :file:`_ext` directory to the `Python path`_ using
   ``sys.path.append``. This should be placed at the top of the file.

#. Update or create the :confval:`extensions` list and add the extension file
   name to the list

For example:

.. code-block:: python

   import sys
   from pathlib import Path

   sys.path.append(str(Path('_ext').resolve()))

   extensions = ['helloworld']

.. tip::

   Because we haven't installed our extension as a `Python package`_, we need to
   modify the `Python path`_ so Sphinx can find our extension. This is why we
   need the call to ``sys.path.append``.

You can now use the extension in a file. For example:

.. code-block:: rst

   Some intro text here...

   .. hello:: world

   Some text with a :hello:`world` role.

The sample above would generate:

.. code-block:: text

   Some intro text here...

   Hello world!

   Some text with a hello world! role.


Further reading
---------------

This is the very basic principle of an extension
that creates a new role and directive.

For a more advanced example, refer to :ref:`tutorial-extend-build`.

If you wish to share your extension across multiple projects or with others,
check out the :ref:`third-party-extensions` section.

.. _docutils: https://docutils.sourceforge.io/
.. _docutils roles: https://docutils.sourceforge.io/docs/howto/rst-roles.html
.. _docutils directives: https://docutils.sourceforge.io/docs/howto/rst-directives.html
.. _docutils nodes: https://docutils.sourceforge.io/docs/ref/doctree.html
.. _PyPI: https://pypi.org/
.. _Python package: https://packaging.python.org/
.. _Python path: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH
