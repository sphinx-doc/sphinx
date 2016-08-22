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

.. a non-local image URI
.. image:: http://www.python.org/logo.png

.. should give a warning
.. literalinclude:: wrongenc.inc
   :language: none

.. a non-existing download

Don't download :download:`this <nonexisting.png>`.

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
