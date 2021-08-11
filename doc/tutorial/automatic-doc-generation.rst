Automatic documentation generation from code
============================================

In the :ref:`previous section <tutorial-describing-objects>` of the tutorial
you manually documented a Python function in Sphinx. However, the description
was out of sync with the code itself, since the function signature was not
the same. Besides, it would be nice to reuse `Python
docstrings <https://www.python.org/dev/peps/pep-0257/#what-is-a-docstring>`_
in the documentation, rather than having to write the information in two
places.

Fortunately, :doc:`autodoc </usage/extensions/autodoc>` provides this
functionality.

Reusing signatures and docstrings with autodoc
----------------------------------------------

To use autodoc, first add it to the list of enabled extensions:

.. code-block:: python
   :caption: docs/source/conf.py
   :emphasize-lines: 4

   extensions = [
       'sphinx.ext.duration',
       'sphinx.ext.doctest',
       'sphinx.ext.autodoc',
   ]

Next, move the content of the ``.. py:function`` directive to the function
docstring in the original Python file and add an optional ``kind`` argument,
as follows:

.. code-block:: python
   :caption: lumache.py
   :emphasize-lines: 1-9

   def get_random_ingredients(kind=None):
       """
       Return a list of random ingredients as strings.

       :param kind: Optional "kind" of ingredients.
       :type kind: list[str] or None
       :raise lumache.InvalidKindError: If the kind is invalid.
       :return: The ingredients list.
       :rtype: list[str]

       """
       return ["shells", "gorgonzola", "parsley"]

Finally, replace the ``.. py:function`` directive from the Sphinx documentation
with :rst:dir:`autofunction`:

.. code-block:: rst
   :caption: docs/source/usage.rst
   :emphasize-lines: 3

   you can use the ``lumache.get_random_ingredients()`` function:

   .. autofunction:: lumache.get_random_ingredients

If you now build the HTML documentation, the output will be the same!
Sphinx took the reStructuredText from the docstring and included it,
also generating proper cross-references.

You can also autogenerate documentation from other objects. For example, add
the code for the ``InvalidKindError`` exception:

.. code-block:: python
   :caption: lumache.py

   class InvalidKindError(Exception):
       """Raised if the kind is invalid."""
       pass

And replace the ``.. py:exception`` directive with :rst:dir:`autoexception`
as follows:

.. code-block:: rst
   :caption: docs/source/usage.rst
   :emphasize-lines: 4

   or ``"veggies"``. Otherwise, :py:func:`lumache.get_random_ingredients`
   will raise an exception.

   .. autoexception:: lumache.InvalidKindError

And again, after running ``make html``, the output will be the same as before.
