:mod:`sphinx.ext.napoleon` -- Support for NumPy and Google style docstrings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: sphinx.ext.napoleon
   :synopsis: Support for NumPy and Google style docstrings

.. moduleauthor:: Rob Ruana

.. versionadded:: 1.3

Napoleon - *Marching toward legible docstrings*
===============================================

.. highlight:: text

Are you tired of writing docstrings that look like this::

    :param path: The path of the file to wrap
    :type path: str
    :param field_storage: The :class:`FileStorage` instance to wrap
    :type field_storage: FileStorage
    :param temporary: Whether or not to delete the file when the File
       instance is destructed
    :type temporary: bool
    :returns: A buffered writable file descriptor
    :rtype: BufferedFileStorage

`ReStructuredText`_ is great, but it creates visually dense, hard to read
`docstrings`_. Compare the jumble above to the same thing rewritten
according to the `Google Python Style Guide`_::

    Args:
        path (str): The path of the file to wrap
        field_storage (FileStorage): The :class:`FileStorage` instance to wrap
        temporary (bool): Whether or not to delete the file when the File
           instance is destructed

    Returns:
        BufferedFileStorage: A buffered writable file descriptor

Much more legible, no?

Napoleon is a :doc:`../extensions` that enables Sphinx to parse both `NumPy`_
and `Google`_ style docstrings - the style recommended by `Khan Academy`_.

Napoleon is a pre-processor that parses `NumPy`_ and `Google`_ style
docstrings and converts them to reStructuredText before Sphinx attempts to
parse them. This happens in an intermediate step while Sphinx is processing
the documentation, so it doesn't modify any of the docstrings in your actual
source code files.

.. _ReStructuredText: http://docutils.sourceforge.net/rst.html
.. _docstrings: https://www.python.org/dev/peps/pep-0287/
.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html
.. _Google:
   http://google.github.io/styleguide/pyguide.html#Comments
.. _NumPy:
   https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _Khan Academy:
   https://github.com/Khan/style-guides/blob/master/style/python.md#docstrings

Getting Started
---------------

1. After :doc:`setting up Sphinx <../tutorial>` to build your docs, enable
   napoleon in the Sphinx `conf.py` file::

       # conf.py

       # Add autodoc and napoleon to the extensions list
       extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

2. Use `sphinx-apidoc` to build your API documentation::

       $ sphinx-apidoc -f -o docs/source projectdir


Docstrings
----------

Napoleon interprets every docstring that :mod:`autodoc <sphinx.ext.autodoc>`
can find, including docstrings on: ``modules``, ``classes``, ``attributes``,
``methods``, ``functions``, and ``variables``. Inside each docstring,
specially formatted `Sections`_ are parsed and converted to
reStructuredText.

All standard reStructuredText formatting still works as expected.


.. _Sections:

Docstring Sections
------------------

All of the following section headers are supported:

    * ``Args`` *(alias of Parameters)*
    * ``Arguments`` *(alias of Parameters)*
    * ``Attributes``
    * ``Example``
    * ``Examples``
    * ``Keyword Args`` *(alias of Keyword Arguments)*
    * ``Keyword Arguments``
    * ``Methods``
    * ``Note``
    * ``Notes``
    * ``Other Parameters``
    * ``Parameters``
    * ``Return`` *(alias of Returns)*
    * ``Returns``
    * ``Raises``
    * ``References``
    * ``See Also``
    * ``Todo``
    * ``Warning``
    * ``Warnings`` *(alias of Warning)*
    * ``Warns``
    * ``Yield`` *(alias of Yields)*
    * ``Yields``

Google vs NumPy
---------------

Napoleon supports two styles of docstrings: `Google`_ and `NumPy`_. The
main difference between the two styles is that Google uses indention to
separate sections, whereas NumPy uses underlines.

Google style:

.. code-block:: python3

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

.. code-block:: python3

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

The `Khan Academy`_ recommends using Google style.

The choice between styles is largely aesthetic, but the two styles should
not be mixed. Choose one style for your project and be consistent with it.

.. seealso::

   For complete examples:

   * :ref:`example_google`
   * :ref:`example_numpy`


Type Annotations
----------------

`PEP 484`_ introduced a standard way to express types in Python code.
This is an alternative to expressing types directly in docstrings.
One benefit of expressing types according to `PEP 484`_ is that
type checkers and IDEs can take advantage of them for static code
analysis.

Google style with Python 3 type annotations::

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

Google style with types in docstrings::

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

.. Note::
   `Python 2/3 compatible annotations`_ aren't currently
   supported by Sphinx and won't show up in the docs.

.. _PEP 484:
   https://www.python.org/dev/peps/pep-0484/

.. _Python 2/3 compatible annotations:
   https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code


Configuration
=============

Listed below are all the settings used by napoleon and their default
values. These settings can be changed in the Sphinx `conf.py` file. Make
sure that both "sphinx.ext.autodoc" and "sphinx.ext.napoleon" are
enabled in `conf.py`::

    # conf.py

    # Add any Sphinx extension module names here, as strings
    extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

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

.. _Google style:
   http://google-styleguide.googlecode.com/svn/trunk/pyguide.html
.. _NumPy style:
   https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt



.. confval:: napoleon_google_docstring

   True to parse `Google style`_ docstrings. False to disable support
   for Google style docstrings. *Defaults to True.*

.. confval:: napoleon_numpy_docstring

   True to parse `NumPy style`_ docstrings. False to disable support
   for NumPy style docstrings. *Defaults to True.*

.. confval:: napoleon_include_init_with_doc

   True to list ``__init___`` docstrings separately from the class
   docstring. False to fall back to Sphinx's default behavior, which
   considers the ``__init___`` docstring as part of the class
   documentation. *Defaults to False.*

   **If True**::

       def __init__(self):
           \"\"\"
           This will be included in the docs because it has a docstring
           \"\"\"

       def __init__(self):
           # This will NOT be included in the docs

.. confval:: napoleon_include_private_with_doc

   True to include private members (like ``_membername``) with docstrings
   in the documentation. False to fall back to Sphinx's default behavior.
   *Defaults to False.*

   **If True**::

       def _included(self):
           """
           This will be included in the docs because it has a docstring
           """
           pass

       def _skipped(self):
           # This will NOT be included in the docs
           pass

.. confval:: napoleon_include_special_with_doc

   True to include special members (like ``__membername__``) with
   docstrings in the documentation. False to fall back to Sphinx's
   default behavior. *Defaults to True.*

   **If True**::

       def __str__(self):
           """
           This will be included in the docs because it has a docstring
           """
           return unicode(self).encode('utf-8')

       def __unicode__(self):
           # This will NOT be included in the docs
           return unicode(self.__class__.__name__)

.. confval:: napoleon_use_admonition_for_examples

   True to use the ``.. admonition::`` directive for the **Example** and
   **Examples** sections. False to use the ``.. rubric::`` directive
   instead. One may look better than the other depending on what HTML
   theme is used. *Defaults to False.*

   This `NumPy style`_ snippet will be converted as follows::

       Example
       -------
       This is just a quick example

   **If True**::

       .. admonition:: Example

          This is just a quick example

   **If False**::

       .. rubric:: Example

       This is just a quick example

.. confval:: napoleon_use_admonition_for_notes

   True to use the ``.. admonition::`` directive for **Notes** sections.
   False to use the ``.. rubric::`` directive instead. *Defaults to False.*

   .. note:: The singular **Note** section will always be converted to a
      ``.. note::`` directive.

   .. seealso::

      :attr:`napoleon_use_admonition_for_examples`

.. confval:: napoleon_use_admonition_for_references

   True to use the ``.. admonition::`` directive for **References**
   sections. False to use the ``.. rubric::`` directive instead.
   *Defaults to False.*

   .. seealso::

      :attr:`napoleon_use_admonition_for_examples`

.. confval:: napoleon_use_ivar

   True to use the ``:ivar:`` role for instance variables. False to use
   the ``.. attribute::`` directive instead. *Defaults to False.*

   This `NumPy style`_ snippet will be converted as follows::

       Attributes
       ----------
       attr1 : int
           Description of `attr1`

   **If True**::

       :ivar attr1: Description of `attr1`
       :vartype attr1: int

   **If False**::

       .. attribute:: attr1

          *int*

          Description of `attr1`

.. confval:: napoleon_use_param

   True to use a ``:param:`` role for each function parameter. False to
   use a single ``:parameters:`` role for all the parameters.
   *Defaults to True.*

   This `NumPy style`_ snippet will be converted as follows::

       Parameters
       ----------
       arg1 : str
           Description of `arg1`
       arg2 : int, optional
           Description of `arg2`, defaults to 0

   **If True**::

       :param arg1: Description of `arg1`
       :type arg1: str
       :param arg2: Description of `arg2`, defaults to 0
       :type arg2: int, optional

   **If False**::

       :parameters: * **arg1** (*str*) --
                      Description of `arg1`
                    * **arg2** (*int, optional*) --
                      Description of `arg2`, defaults to 0

.. confval:: napoleon_use_keyword

   True to use a ``:keyword:`` role for each function keyword argument.
   False to use a single ``:keyword arguments:`` role for all the
   keywords.
   *Defaults to True.*

   This behaves similarly to  :attr:`napoleon_use_param`. Note unlike docutils,
   ``:keyword:`` and ``:param:`` will not be treated the same way - there will
   be a separate "Keyword Arguments" section, rendered in the same fashion as
   "Parameters" section (type links created if possible)

   .. seealso::

      :attr:`napoleon_use_param`

.. confval:: napoleon_use_rtype

   True to use the ``:rtype:`` role for the return type. False to output
   the return type inline with the description. *Defaults to True.*

   This `NumPy style`_ snippet will be converted as follows::

       Returns
       -------
       bool
           True if successful, False otherwise

   **If True**::

       :returns: True if successful, False otherwise
       :rtype: bool

   **If False**::

       :returns: *bool* -- True if successful, False otherwise
