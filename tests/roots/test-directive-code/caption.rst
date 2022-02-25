Caption
=======

References
----------

See :numref:`name *test* rb` and :numref:`name **test** py`.

See :ref:`Ruby <name *test* rb>` and :ref:`Python <name **test** py>`.


Code blocks
-----------

.. code-block:: ruby
   :caption: caption *test* rb

   def ruby?
       false
   end


Literal Include
---------------

.. literalinclude:: literal.inc
   :language: python
   :caption: caption **test** py
   :lines: 10-11


Named Code blocks
-----------------

.. code-block:: ruby
   :name: name *test* rb
   :caption: caption *test* rbnamed

   def ruby?
       false
   end


Named Literal Include
---------------------

.. literalinclude:: literal.inc
   :language: python
   :name: name **test** py
   :caption: caption **test** pynamed
   :lines: 10-11

