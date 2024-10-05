test-warnings
=============

.. automodule:: autodoc_fodder
   :no-index:

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

.. a non-existing download

Don't download :download:`this <nonexisting.png>`.

.. Invalid index markup
.. index::
   single:
   pair:
   seealso:

.. Invalid code-block
.. code-block:: c

   import sys

   sys.stdout.write('hello world!\n')

.. unknown option

This used to crash: :option:`&option`

.. missing citation

[missing]_ citation
