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
