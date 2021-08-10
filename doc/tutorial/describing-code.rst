Describing code in Sphinx
=========================

In the previous sections of the tutorial you can read how to write narrative
or prose documentation in Sphinx. In this section you will describe code
objects instead.

Documenting Python objects
--------------------------

Sphinx offers several roles and directives to document Python objects,
all grouped together in the Python
:doc:`domain </usage/restructuredtext/domains>`. For example, you can
use the :rst:dir:`py:function` directive to document a Python function,
as follows:

.. code-block:: rst
   :caption: docs/source/usage.rst

   Creating recipes
   ----------------

   To retrieve a list of random ingredients,
   you can use the ``lumache.get_random_ingredients()`` function:

   .. py:function:: lumache.get_random_ingredients([kind=None])

      Return a list of random ingredients as strings.

      :param kind: Optional "kind" of ingredients.
      :type kind: list[str] or None
      :return: The ingredients list.
      :rtype: list[str]

Which will render like this:

.. figure:: /_static/tutorial/lumache-py-function.png
   :width: 80%
   :align: center
   :alt: HTML result of documenting a Python function in Sphinx

   HTML result of documenting a Python function in Sphinx

Notice several things:

- Sphinx parsed the argument of the ``.. py:function`` directive and
  highlighted the module, the function name, and the parameters appropriately.
- Putting a parameter inside square brackets usually conveys that it is
  optional (although it is not mandatory to use this syntax).
- The directive content includes a one-line description of the function,
  as well as a :ref:`field list <rst-field-lists>` containing the function
  parameter, its expected type, the return value, and the return type.

.. note::

   Since Python is the default :term:`domain`, you can write
   ``.. function::`` directly without having to prefix the directive with
   ``py:``.

Cross-referencing Python objects
--------------------------------

By default, most of these directives generate entities that can be
cross-referenced from any part of the documentation by using
:ref:`a corresponding role <python-roles>`. For the case of functions,
you can use :rst:role:`py:func` for that, as follows:

.. code-block:: rst
   :caption: docs/source/usage.rst

   The ``kind`` parameter should be either ``"meat"``, ``"fish"``,
   or ``"veggies"``. Otherwise, :py:func:`lumache.get_random_ingredients`
   will raise an exception.

In some contexts, Sphinx will generate a cross-reference automatically just
by using the name of the object, without you having to explicitly use a role
for that. For example, you can describe the custom exception raised by the
function using the :rst:dir:`py:exception` directive:

.. code-block:: rst
   :caption: docs/source/usage.rst

   .. py:exception:: lumache.InvalidKindError

      Raised if the kind is invalid.

Then, add this exception to the original description of the function:

.. code-block:: rst
   :caption: docs/source/usage.rst
   :emphasize-lines: 7

   .. py:function:: lumache.get_random_ingredients([kind=None])

      Return a list of random ingredients as strings.

      :param kind: Optional "kind" of ingredients.
      :type kind: list[str] or None
      :raise lumache.InvalidKindError: If the kind is invalid.
      :return: The ingredients list.
      :rtype: list[str]

And finally, this is how the result would look like:

.. figure:: /_static/tutorial/lumache-py-function-full.png
   :width: 80%
   :align: center
   :alt: HTML result of documenting a Python function in Sphinx
         with cross-references

   HTML result of documenting a Python function in Sphinx with cross-references

Beautiful, isn't it?

Including doctests in your documentation
----------------------------------------

Since you are now describing code from a Python library, it will become useful
to keep both the documentation and the code as synchronized as possible.
One of the ways to do that in Sphinx is to include code snippets in the
documentation, called *doctests*, that are executed when the documentation is
built.

To demonstrate doctests and other Sphinx features covered in this tutorial,
you will need to setup some basic Python infrastructure first.

Preparing the Python library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Begin by activating the virtual environment (as seen in the :ref:`getting
started <tutorial-getting-started>` section of the tutorial) and install
`flit <https://pypi.org/project/flit/>`_ on it:

.. code-block:: console

   $ source .venv/bin/activate
   (.venv) $ python -m pip install "flit~=3.3"

Next, create two files on the same level as ``README.rst``: ``pyproject.toml``
and ``lumache.py``, with these contents:

.. code-block:: toml
   :caption: pyproject.toml

   [build-system]
   requires = ["flit_core >=3.2,<4"]
   build-backend = "flit_core.buildapi"

   [project]
   name = "lumache"
   authors = [{name = "Graziella", email = "graziella@lumache"}]
   dynamic = ["version", "description"]

.. code-block:: python
   :caption: lumache.py

   """
   Lumache - Python library for cooks and food lovers.
   """

   __version__ = "0.1.0"

And finally, install your own code and check that importing it works:

.. code-block:: console

   (.venv) $ flit install --symlink
   ...
   (.venv) $ python -c 'import lumache; print("OK!")'
   OK!

Congratulations! You have created a basic Python library.

.. note::

   The ``pyproject.toml`` file you created above is required so that
   your library can be installed. On the other hand,
   ``flit install --symlink`` is an alternative to ``pip install .``
   that removes the need to reinstall the library every time you make
   a change, which is convenient.

   An alternative is to not create ``pyproject.toml`` at all,
   and setting the :envvar:`PYTHONPATH`, :py:data:`sys.path`, or
   equivalent. However, the ``pyproject.toml`` approach is more robust.
