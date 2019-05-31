Developing a "Hello world" extension
====================================

The objective of this tutorial is to create a very basic extension that adds a
new directive. This directive will output a paragraph containing "hello world".

Only basic information is provided in this tutorial. For more information, refer
to the :doc:`other tutorials <index>` that go into more details.

.. warning::

   For this extension, you will need some basic understanding of docutils_
   and Python.


Overview
--------

We want the extension to add the following to Sphinx:

* A ``helloworld`` directive, that will simply output the text "hello world".


Prerequisites
-------------

We will not be distributing this plugin via `PyPI`_ and will instead include it
as part of an existing project. This means you will need to use an existing
project or create a new one using :program:`sphinx-quickstart`.

We assume you are using separate source (:file:`source`) and build
(:file:`build`) folders. Your extension file could be in any folder of your
project. In our case, let's do the following:

#. Create an :file:`_ext` folder in :file:`source`
#. Create a new Python file in the :file:`_ext` folder called
   :file:`helloworld.py`

Here is an example of the folder structure you might obtain:

.. code-block:: text

      └── source
          ├── _ext
          │   └── helloworld.py
          ├── _static
          ├── conf.py
          ├── somefolder
          ├── index.rst
          ├── somefile.rst
          └── someotherfile.rst


Writing the extension
---------------------

Open :file:`helloworld.py` and paste the following code in it:

.. literalinclude:: examples/helloworld.py
   :language: python
   :linenos:

Some essential things are happening in this example, and you will see them for
all directives.

.. rubric:: The directive class

Our new directive is declared in the ``HelloWorld`` class.

.. literalinclude:: examples/helloworld.py
   :language: python
   :linenos:
   :lines: 5-9

This class extends the docutils_' ``Directive`` class. All extensions that
create directives should extend this class.

.. seealso::

   `The docutils documentation on creating directives <docutils directives_>`_

This class contains a ``run`` method.  This method is a requirement and it is
part of every directive.  It contains the main logic of the directive and it
returns a list of docutils nodes to be processed by Sphinx. These nodes are
docutils' way of representing the content of a document. There are many types of
nodes available: text, paragraph, reference, table, etc.

.. seealso::

   `The docutils documentation on nodes <docutils nodes_>`_

The ``nodes.paragraph`` class creates a new paragraph node. A paragraph
node typically contains some text that we can set during instantiation using
the ``text`` parameter.

.. rubric:: The ``setup`` function

.. currentmodule:: sphinx.application

This function is a requirement. We use it to plug our new directive into
Sphinx.

.. literalinclude:: examples/helloworld.py
   :language: python
   :linenos:
   :lines: 12-

The simplest thing you can do it call the :meth:`~Sphinx.add_directive` method,
which is what we've done here. For this particular call, the first argument is
the name of the directive itself as used in a reST file. In this case, we would
use ``helloworld``. For example:

.. code-block:: rst

   Some intro text here...

   .. helloworld::

   Some more text here...

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

   import os
   import sys

   sys.path.append(os.path.abspath("./_ext"))

   extensions = ['helloworld']

.. tip::

   We're not distributing this extension as a `Python package`_, we need to
   modify the `Python path`_ so Sphinx can find our extension. This is why we
   need the call to ``sys.path.append``.

You can now use the extension in a file. For example:

.. code-block:: rst

   Some intro text here...

   .. helloworld::

   Some more text here...

The sample above would generate:

.. code-block:: text

   Some intro text here...

   Hello World!

   Some more text here...


Further reading
---------------

This is the very basic principle of an extension that creates a new directive.

For a more advanced example, refer to :doc:`todo`.


.. _docutils: http://docutils.sourceforge.net/
.. _docutils directives: http://docutils.sourceforge.net/docs/howto/rst-directives.html
.. _docutils nodes: http://docutils.sourceforge.net/docs/ref/doctree.html
.. _PyPI: https://pypi.org/
.. _Python package: https://packaging.python.org/
.. _Python path: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH
