test-warnings
=============

.. automodule:: autodoc_fodder
   :noindex:

   .. autoclass:: MarkupError

.. a non-existing image with direct filename
.. image:: foo.png

.. a non-existing image with .*
.. image:: foo.*

.. an SVG image (for HTML at least)
.. image:: svgimg.*

.. should give a warning
.. literalinclude:: wrongenc.inc
   :language: none

.. an undefined variable and non-existing download

Fail to format and don't download :download:`this <{{undefined_variable}}>`.

.. Invalid index markup
.. index::
   single:
   pair:
   keyword:

.. Invalid code-block
.. code-block:: c

   import sys

   sys.stdout.write('hello world!\n')

.. unknown option

This used to crash: :option:`&option`

.. missing citation

[missing]_ citation
