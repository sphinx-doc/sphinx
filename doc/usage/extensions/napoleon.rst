:mod:`sphinx.ext.napoleon` -- Support for NumPy and Google style docstrings
===========================================================================

.. module:: sphinx.ext.napoleon
   :synopsis: Support for NumPy and Google style docstrings

.. moduleauthor:: Rob Ruana

.. versionadded:: 1.3

.. role:: code-py(code)
   :language: Python

Overview
--------

Are you tired of writing docstrings that look like this:

.. code-block:: rst

    :param path: The path of the file to wrap
    :type path: str
    :param field_storage: The :class:`FileStorage` instance to wrap
    :type field_storage: FileStorage
    :param temporary: Whether or not to delete the file when the File
       instance is destructed
    :type temporary: bool
    :returns: A buffered writable file descriptor
    :rtype: BufferedFileStorage

`reStructuredText`_ is great, but it creates visually dense, hard to read
:pep:`docstrings <287>`. Compare the jumble above to the same thing rewritten
according to the `Google Python Style Guide`_:

.. code-block:: text

    Args:
        path (str): The path of the file to wrap
        field_storage (FileStorage): The :class:`FileStorage` instance to wrap
        temporary (bool): Whether or not to delete the file when the File
           instance is destructed

    Returns:
        BufferedFileStorage: A buffered writable file descriptor

Much more legible, no?

Napoleon is a :term:`extension` that enables Sphinx to parse both `NumPy`_ and
`Google`_ style docstrings - the style recommended by `Khan Academy`_.

Napoleon is a pre-processor that parses `NumPy`_ and `Google`_ style
docstrings and converts them to reStructuredText before Sphinx attempts to
parse them. This happens in an intermediate step while Sphinx is processing
the documentation, so it doesn't modify any of the docstrings in your actual
source code files.

.. _ReStructuredText: https://docutils.sourceforge.io/rst.html
.. _Google Python Style Guide:
   https://google.github.io/styleguide/pyguide.html
.. _Google:
   https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
.. _NumPy:
   https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard
.. _Khan Academy:
   https://github.com/Khan/style-guides/blob/master/style/python.md#docstrings

Getting Started
~~~~~~~~~~~~~~~

1. After :doc:`setting up Sphinx </usage/quickstart>` to build your docs,
   enable napoleon in the Sphinx ``conf.py`` file:

   .. code-block:: python

       # conf.py

       # Add napoleon to the extensions list
       extensions = ['sphinx.ext.napoleon']

2. Use ``sphinx-apidoc`` to build your API documentation:

   .. code-block:: console

       $ sphinx-apidoc -f -o docs/source projectdir


Docstrings
~~~~~~~~~~

Napoleon interprets every docstring that :mod:`autodoc <sphinx.ext.autodoc>`
can find, including docstrings on: ``modules``, ``classes``, ``attributes``,
``methods``, ``functions``, and ``variables``. Inside each docstring,
specially formatted `Sections`_ are parsed and converted to
reStructuredText.

All standard reStructuredText formatting still works as expected.


.. _Sections:

Docstring Sections
~~~~~~~~~~~~~~~~~~

All of the following section headers are supported:

* ``Args`` *(alias of Parameters)*
* ``Arguments`` *(alias of Parameters)*
* ``Attention``
* ``Attributes``
* ``Caution``
* ``Danger``
* ``Error``
* ``Example``
* ``Examples``
* ``Hint``
* ``Important``
* ``Keyword Args`` *(alias of Keyword Arguments)*
* ``Keyword Arguments``
* ``Methods``
* ``Note``
* ``Notes``
* ``Other Parameters``
* ``Parameters``
* ``Return`` *(alias of Returns)*
* ``Returns``
* ``Raise`` *(alias of Raises)*
* ``Raises``
* ``References``
* ``See Also``
* ``Tip``
* ``Todo``
* ``Warning``
* ``Warnings`` *(alias of Warning)*
* ``Warn`` *(alias of Warns)*
* ``Warns``
* ``Yield`` *(alias of Yields)*
* ``Yields``

Google vs NumPy
~~~~~~~~~~~~~~~

Napoleon supports two styles of docstrings: `Google`_ and `NumPy`_. The
main difference between the two styles is that Google uses indentation to
separate sections, whereas NumPy uses underlines.

Google style:

.. code-block:: python

    def func(arg1, arg2):
        """Summary line.

        Extended description of function.

        Args:
            arg1 (int): Description of arg1
            arg2 (str): Description of arg2

        Returns:
            bool: Description of return value

        """
        return True

NumPy style:

.. code-block:: python

    def func(arg1, arg2):
        """Summary line.

        Extended description of function.

        Parameters
        ----------
        arg1 : int
            Description of arg1
        arg2 : str
            Description of arg2

        Returns
        -------
        bool
            Description of return value

        """
        return True

NumPy style tends to require more vertical space, whereas Google style
tends to use more horizontal space. Google style tends to be easier to
read for short and simple docstrings, whereas NumPy style tends be easier
to read for long and in-depth docstrings.

The choice between styles is largely aesthetic, but the two styles should
not be mixed. Choose one style for your project and be consistent with it.

.. seealso::

   For complete examples:

   * :ref:`example_google`
   * :ref:`example_numpy`


Type Annotations
~~~~~~~~~~~~~~~~

:pep:`484` introduced a standard way to express types in Python code.
This is an alternative to expressing types directly in docstrings.
One benefit of expressing types according to :pep:`484` is that
type checkers and IDEs can take advantage of them for static code
analysis. :pep:`484` was then extended by :pep:`526` which introduced
a similar way to annotate variables (and attributes).

Google style with type annotations:

.. code-block:: python

    def func(arg1: int, arg2: str) -> bool:
        """Summary line.

        Extended description of function.

        Args:
            arg1: Description of arg1
            arg2: Description of arg2

        Returns:
            Description of return value

        """
        return True

    class Class:
        """Summary line.

        Extended description of class

        Attributes:
            attr1: Description of attr1
            attr2: Description of attr2
        """

        attr1: int
        attr2: str

Google style with types in docstrings:

.. code-block:: python

    def func(arg1, arg2):
        """Summary line.

        Extended description of function.

        Args:
            arg1 (int): Description of arg1
            arg2 (str): Description of arg2

        Returns:
            bool: Description of return value

        """
        return True

    class Class:
        """Summary line.

        Extended description of class

        Attributes:
            attr1 (int): Description of attr1
            attr2 (str): Description of attr2
        """


Configuration
-------------

Listed below are all the settings used by napoleon and their default
values. These settings can be changed in the Sphinx ``conf.py`` file. Make
sure that "sphinx.ext.napoleon" is enabled in ``conf.py``:

.. code-block:: python

    # conf.py

    # Add any Sphinx extension module names here, as strings
    extensions = ['sphinx.ext.napoleon']

    # Napoleon settings
    napoleon_google_docstring = True
    napoleon_numpy_docstring = True
    napoleon_include_init_with_doc = False
    napoleon_include_private_with_doc = False
    napoleon_include_special_with_doc = True
    napoleon_use_admonition_for_examples = False
    napoleon_use_admonition_for_notes = False
    napoleon_use_admonition_for_references = False
    napoleon_use_ivar = False
    napoleon_use_param = True
    napoleon_use_rtype = True
    napoleon_preprocess_types = False
    napoleon_type_aliases = None
    napoleon_attr_annotations = True

.. _Google style:
   https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
.. _NumPy style:
   https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard

.. confval:: napoleon_google_docstring
   :type: :code-py:`bool`
   :default: :code-py:`True`

   True to parse `Google style`_ docstrings. False to disable support
   for Google style docstrings.

.. confval:: napoleon_numpy_docstring
   :type: :code-py:`bool`
   :default: :code-py:`True`

   True to parse `NumPy style`_ docstrings. False to disable support
   for NumPy style docstrings.

.. confval:: napoleon_include_init_with_doc
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to list ``__init___`` docstrings separately from the class
   docstring. False to fall back to Sphinx's default behavior, which
   considers the ``__init___`` docstring as part of the class
   documentation.

   **If True**:

   .. code-block:: python

       def __init__(self):
           """
           This will be included in the docs because it has a docstring
           """

       def __init__(self):
           # This will NOT be included in the docs

.. confval:: napoleon_include_private_with_doc
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to include private members (like ``_membername``) with docstrings
   in the documentation. False to fall back to Sphinx's default behavior.

   **If True**:

   .. code-block:: python

       def _included(self):
           """
           This will be included in the docs because it has a docstring
           """
           pass

       def _skipped(self):
           # This will NOT be included in the docs
           pass

.. confval:: napoleon_include_special_with_doc
   :type: :code-py:`bool`
   :default: :code-py:`True`

   True to include special members (like ``__membername__``) with
   docstrings in the documentation. False to fall back to Sphinx's
   default behavior.

   **If True**:

   .. code-block:: python

       def __str__(self):
           """
           This will be included in the docs because it has a docstring
           """
           return unicode(self).encode('utf-8')

       def __unicode__(self):
           # This will NOT be included in the docs
           return unicode(self.__class__.__name__)

.. confval:: napoleon_use_admonition_for_examples
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to use the ``.. admonition::`` directive for the **Example** and
   **Examples** sections. False to use the ``.. rubric::`` directive
   instead. One may look better than the other depending on what HTML
   theme is used.

   This `NumPy style`_ snippet will be converted as follows:

   .. code-block:: text

       Example
       -------
       This is just a quick example

   **If True**:

   .. code-block:: rst

       .. admonition:: Example

          This is just a quick example

   **If False**:

   .. code-block:: rst

       .. rubric:: Example

       This is just a quick example

.. confval:: napoleon_use_admonition_for_notes
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to use the ``.. admonition::`` directive for **Notes** sections.
   False to use the ``.. rubric::`` directive instead.

   .. note:: The singular **Note** section will always be converted to a
      ``.. note::`` directive.

   .. seealso::

      :confval:`napoleon_use_admonition_for_examples`

.. confval:: napoleon_use_admonition_for_references
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to use the ``.. admonition::`` directive for **References**
   sections. False to use the ``.. rubric::`` directive instead.

   .. seealso::

      :confval:`napoleon_use_admonition_for_examples`

.. confval:: napoleon_use_ivar
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to use the ``:ivar:`` role for instance variables. False to use
   the ``.. attribute::`` directive instead.

   This `NumPy style`_ snippet will be converted as follows:

   .. code-block:: text

       Attributes
       ----------
       attr1 : int
           Description of `attr1`

   **If True**:

   .. code-block:: rst

       :ivar attr1: Description of `attr1`
       :vartype attr1: int

   **If False**:

   .. code-block:: rst

       .. attribute:: attr1

          Description of `attr1`

          :type: int

.. confval:: napoleon_use_param
   :type: :code-py:`bool`
   :default: :code-py:`True`

   True to use a ``:param:`` role for each function parameter. False to
   use a single ``:parameters:`` role for all the parameters.

   This `NumPy style`_ snippet will be converted as follows:

   .. code-block:: text

       Parameters
       ----------
       arg1 : str
           Description of `arg1`
       arg2 : int, optional
           Description of `arg2`, defaults to 0

   **If True**:

   .. code-block:: rst

       :param arg1: Description of `arg1`
       :type arg1: str
       :param arg2: Description of `arg2`, defaults to 0
       :type arg2: :class:`int`, *optional*

   **If False**:

   .. code-block:: rst

       :parameters: * **arg1** (*str*) --
                      Description of `arg1`
                    * **arg2** (*int, optional*) --
                      Description of `arg2`, defaults to 0

.. confval:: napoleon_use_keyword
   :type: :code-py:`bool`
   :default: :code-py:`True`

   True to use a ``:keyword:`` role for each function keyword argument.
   False to use a single ``:keyword arguments:`` role for all the
   keywords.

   This behaves similarly to :confval:`napoleon_use_param`. Note unlike docutils,
   ``:keyword:`` and ``:param:`` will not be treated the same way - there will
   be a separate "Keyword Arguments" section, rendered in the same fashion as
   "Parameters" section (type links created if possible)

   .. seealso::

      :confval:`napoleon_use_param`

.. confval:: napoleon_use_rtype
   :type: :code-py:`bool`
   :default: :code-py:`True`

   True to use the ``:rtype:`` role for the return type. False to output
   the return type inline with the description.

   This `NumPy style`_ snippet will be converted as follows:

   .. code-block:: text

       Returns
       -------
       bool
           True if successful, False otherwise

   **If True**:

   .. code-block:: rst

       :returns: True if successful, False otherwise
       :rtype: bool

   **If False**:

   .. code-block:: rst

       :returns: *bool* -- True if successful, False otherwise

.. confval:: napoleon_preprocess_types
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to convert the type definitions in the docstrings as references.

   .. versionadded:: 3.2.1
   .. versionchanged:: 3.5

      Do preprocess the Google style docstrings also.

.. confval:: napoleon_type_aliases
   :type: :code-py:`dict[str, str] | None`
   :default: :code-py:`None`

   A mapping to translate type names to other names or references. Works
   only when ``napoleon_use_param = True``.

   With:

   .. code-block:: python

       napoleon_type_aliases = {
           "CustomType": "mypackage.CustomType",
           "dict-like": ":term:`dict-like <mapping>`",
       }

   This `NumPy style`_ snippet:

   .. code-block:: text

       Parameters
       ----------
       arg1 : CustomType
           Description of `arg1`
       arg2 : dict-like
           Description of `arg2`

   becomes:

   .. code-block:: rst

       :param arg1: Description of `arg1`
       :type arg1: mypackage.CustomType
       :param arg2: Description of `arg2`
       :type arg2: :term:`dict-like <mapping>`

   .. versionadded:: 3.2

.. confval:: napoleon_attr_annotations
   :type: :code-py:`bool`
   :default: :code-py:`True`

   True to allow using :pep:`526` attributes annotations in classes.
   If an attribute is documented in the docstring without a type and
   has an annotation in the class body, that type is used.

   .. versionadded:: 3.4

.. confval:: napoleon_custom_sections
   :type: :code-py:`Sequence[str | tuple[str, str]] | None`
   :default: :code-py:`None`

   Add a list of custom sections to include, expanding the list of parsed sections.

   The entries can either be strings or tuples, depending on the intention:

   * To create a custom "generic" section, just pass a string.
   * To create an alias for an existing section, pass a tuple containing the
     alias name and the original, in that order.
   * To create a custom section that displays like the parameters or returns
     section, pass a tuple containing the custom section name and a string
     value, "params_style" or "returns_style".

   If an entry is just a string, it is interpreted as a header for a generic
   section. If the entry is a tuple/list/indexed container, the first entry
   is the name of the section, the second is the section key to emulate. If the
   second entry value is "params_style" or "returns_style", the custom section
   will be displayed like the parameters section or returns section.

   .. versionadded:: 1.8
   .. versionchanged:: 3.5
      Support ``params_style`` and ``returns_style``
