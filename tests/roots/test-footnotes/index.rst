===============
test-footenotes
===============

.. toctree::

   bar
   baz

.. contents::
   :local:

The section with a reference to [AuthorYear]_
=============================================

.. figure:: rimg.png

   This is the figure caption with a reference to [AuthorYear]_.

.. list-table:: The table title with a reference to [AuthorYear]_
   :header-rows: 1

   * - Header1
     - Header2
   * - Content
     - Content

.. rubric:: The rubric title with a reference to [AuthorYear]_

.. [#] First

* First footnote: [#]_
* Second footnote: [1]_
* `Sphinx <http://sphinx-doc.org/>`_
* Third footnote: [#]_
* `URL including tilde <http://sphinx-doc.org/~test/>`_
* GitHub Page: `https://github.com/sphinx-doc/sphinx <https://github.com/sphinx-doc/sphinx>`_
* Mailing list: `sphinx-dev@googlegroups.com <mailto:sphinx-dev@googlegroups.com>`_

.. [AuthorYear] Author, Title, Year
.. [1] Second
.. [#] Third

The section with a reference to [#]_
=====================================

.. [#] Footnote in section

`URL in term <http://sphinx-doc.org/>`_
    Description Description Description ...

Footnote in term [#]_
    Description Description Description ...

    `Term in deflist <http://sphinx-doc.org/>`_
        Description2

.. [#] Footnote in term

.. figure:: rimg.png

   This is the figure caption with a footnote to [#]_.

.. [#] Footnote in caption

.. list-table:: footnote [#]_ in caption of normal table
    :widths: 1 1
    :header-rows: 1

    * - name
      - desc
    * - a
      - b
    * - a
      - b

.. [#] Foot note in table

.. list-table:: footnote [#]_ in caption [#]_ of longtable
    :widths: 1 1
    :header-rows: 1

    * - name
      - desc
    * - This is a reference to the code-block in the footnote:
        :ref:`codeblockinfootnote`
      - This is one more footnote with some code in it [#]_.
    * - This is a reference to the other code block:
        :ref:`codeblockinanotherfootnote`
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b
    * - a
      - b

.. [#] Foot note in longtable

.. [#] Second footnote in caption of longtable

       .. code-block:: python
          :caption: I am in a footnote
          :name: codeblockinfootnote

          def foo(x,y):
              return x+y

.. [#] Third footnote in longtable

       .. code-block:: python
          :caption: I am also in a footnote
          :name: codeblockinanotherfootnote

          def bar(x,y):
              return x+y
