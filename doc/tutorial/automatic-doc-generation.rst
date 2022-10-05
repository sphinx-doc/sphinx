Automatic documentation generation from code
============================================

In the :ref:`previous section <tutorial-describing-objects>` of the tutorial
you manually documented a Python function in Sphinx. However, the description
was out of sync with the code itself, since the function signature was not
the same. Besides, it would be nice to reuse :pep:`Python docstrings
<257#what-is-a-docstring>` in the documentation, rather than having to write
the information in two places.

Fortunately, :doc:`the autodoc extension </usage/extensions/autodoc>` provides this
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
docstring in the original Python file, as follows:

.. code-block:: python
   :caption: lumache.py
   :emphasize-lines: 2-11

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
With the advantage that it is generated from the code itself.
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

Generating comprehensive API references
---------------------------------------

While using ``sphinx.ext.autodoc`` makes keeping the code and the documentation
in sync much easier, it still requires you to write an ``auto*`` directive
for every object you want to document. Sphinx provides yet another level of
automation: the :doc:`autosummary </usage/extensions/autosummary>` extension.

The :rst:dir:`autosummary` directive generates documents that contain all the
necessary ``autodoc`` directives. To use it, first enable the autosummary
extension:

.. code-block:: python
   :caption: docs/source/conf.py
   :emphasize-lines: 5

   extensions = [
      'sphinx.ext.duration',
      'sphinx.ext.doctest',
      'sphinx.ext.autodoc',
      'sphinx.ext.autosummary',
   ]

Next, create a new ``api.rst`` file with these contents:

.. code-block:: rst
   :caption: docs/source/api.rst

   API
   ===

   .. autosummary::
      :toctree: generated

      lumache

Remember to include the new document in the root toctree:

.. code-block:: rst
   :caption: docs/source/index.rst
   :emphasize-lines: 7

   Contents
   --------

   .. toctree::

      usage
      api

Finally, after you build the HTML documentation running ``make html``, it will
contain two new pages:

- ``api.html``, corresponding to ``docs/source/api.rst`` and containing a table
  with the objects you included in the ``autosummary`` directive (in this case,
  only one).
- ``generated/lumache.html``, corresponding to a newly created reST file
  ``generated/lumache.rst`` and containing a summary of members of the module,
  in this case one function and one exception.

.. figure:: /_static/tutorial/lumache-autosummary.png
   :width: 80%
   :align: center
   :alt: Summary page created by autosummary

   Summary page created by autosummary

Each of the links in the summary page will take you to the places where you
originally used the corresponding ``autodoc`` directive, in this case in the
``usage.rst`` document.

.. note::

   The generated files are based on `Jinja2
   templates <https://jinja2docs.readthedocs.io/>`_ that
   :ref:`can be customized <autosummary-customizing-templates>`,
   but that is out of scope for this tutorial.
