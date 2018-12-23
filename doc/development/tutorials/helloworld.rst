Developing a "Hello world" directive
====================================

The objective of this tutorial is to create a very basic extension that adds a new
directive that outputs a paragraph containing `hello world`.

Only basic information is provided in this tutorial. For more information,
refer to the :doc:`other tutorials <index>` that go into more
details.

.. warning:: For this extension, you will need some basic understanding of docutils_
   and Python.

Creating a new extension file
-----------------------------

Your extension file could be in any folder of your project. In our case,
let's do the following:

#. Create an :file:`_ext` folder in :file:`source`.
#. Create a new Python file in the :file:`_ext` folder called
   :file:`helloworld.py`.

   Here is an example of the folder structure you might obtain:

   .. code-block:: text

         └── source
             ├── _ext
             │   └── helloworld.py
             ├── _static
             ├── _themes
             ├── conf.py
             ├── somefolder
             ├── somefile.rst
             └── someotherfile.rst

Writing the extension
---------------------

Open :file:`helloworld.py` and paste the following code in it:

.. code-block:: python

   from docutils import nodes
   from docutils.parsers.rst import Directive


   class HelloWorld(Directive):
       def run(self):
           paragraph_node = nodes.paragraph(text='Hello World!')
           return [paragraph_node]


   def setup(app):
       app.add_directive("helloworld", HelloWorld)


Some essential things are happening in this example, and you will see them
in all directives:

.. rubric:: Directive declaration

Our new directive is declared in the ``HelloWorld`` class, it extends
docutils_' ``Directive`` class. All extensions that create directives
should extend this class.

.. rubric:: ``run`` method

This method is a requirement and it is part of every directive. It contains
the main logic of the directive and it returns a list of docutils nodes to
be processed by Sphinx.

.. seealso::

   :doc:`todo`

.. rubric:: docutils nodes

The ``run`` method returns a list of nodes. Nodes are docutils' way of
representing the content of a document. There are many types of nodes
available: text, paragraph, reference, table, etc.

.. seealso::

   `The docutils documentation on nodes <docutils nodes>`_

The ``nodes.paragraph`` class creates a new paragraph node. A paragraph
node typically contains some text that we can set during instantiation using
the ``text`` parameter.

.. rubric:: ``setup`` function

This function is a requirement. We use it to plug our new directive into
Sphinx.
The simplest thing you can do it call the ``app.add_directive`` method.

.. note::

   The first argument is the name of the directive itself as used in an rST file.

   In our case, we would use ``helloworld``:

   .. code-block:: rst

      Some intro text here...

      .. helloworld::

      Some more text here...


Updating the conf.py file
-------------------------

The extension file has to be declared in your :file:`conf.py` file to make
Sphinx aware of it:

#. Open :file:`conf.py`. It is in the :file:`source` folder by default.
#. Add ``sys.path.append(os.path.abspath("./_ext"))`` before
   the ``extensions`` variable declaration (if it exists).
#. Update or create the ``extensions`` list and add the
   extension file name to the list:

   .. code-block:: python

      extensions.append('helloworld')

You can now use the extension.

.. admonition:: Example

   .. code-block:: rst

      Some intro text here...

      .. helloworld::

      Some more text here...

   The sample above would generate:

   .. code-block:: text

      Some intro text here...

      Hello World!

      Some more text here...

This is the very basic principle of an extension that creates a new directive.

For a more advanced example, refer to :doc:`todo`.

Further reading
---------------

You can create your own nodes if needed, refer to the
:doc:`todo` for more information.

.. _docutils: http://docutils.sourceforge.net/
.. _`docutils nodes`: http://docutils.sourceforge.net/docs/ref/doctree.html