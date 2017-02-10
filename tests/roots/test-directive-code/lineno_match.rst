Literal Includes with Line Numbers Matching
===========================================

.. literalinclude:: literal.inc
   :language: python
   :pyobject: Foo
   :lineno-match:

.. literalinclude:: literal.inc
   :language: python
   :lines: 5-6,7,8-9
   :lineno-match:

.. literalinclude:: literal.inc
   :language: python
   :start-after: pass
   :lineno-match:

.. literalinclude:: literal.inc
   :language: python
   :start-after: Literally
   :lines: 1,2
   :lineno-match:

.. literalinclude:: literal.inc
   :language: python
   :start-at: class Bar:
   :end-at: pass
   :lineno-match:

.. literalinclude:: empty.inc
   :lineno-match:
