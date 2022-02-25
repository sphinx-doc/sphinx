dedent option
-------------

.. code-block::

   First line
   Second line
       Third line
   Fourth line

ReST has no fixed indent and only a change in indention is significant not the amount [1]_.
Thus, the following code inside the code block is not indent even it looks so with respect to the previous block.

.. code-block::

       First line
       Second line
           Third line
       Fourth line

Having an option "fixates" the indent to be 3 spaces, thus the code inside the code block is indented by 4 spaces.

.. code-block::
   :class: dummy

       First line
       Second line
           Third line
       Fourth line

The code has 6 spaces indent, minus 4 spaces dedent should yield a 2 space indented code in the output.

.. code-block::
   :dedent: 4

         First line
         Second line
             Third line
         Fourth line

Dedenting by zero, should not strip any spaces and be a no-op.

.. note::
   This can be used as an alternative to ``:class: dummy`` above, to fixate the ReST indention of the block.

.. code-block::
   :dedent: 0

       First line
       Second line
           Third line
       Fourth line

Dedent without argument should autostrip common whitespace at the beginning.

.. code-block::
   :dedent:

       First line
       Second line
           Third line
       Fourth line

.. [1] https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#indentation
