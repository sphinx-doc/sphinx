Literal Includes with Highlighted Lines
=======================================

Using absolute lines as highlights:

.. literalinclude:: target.py
   :language: python
   :emphasize-lines: 5-6, 13-15, 24-

Now using text contents instead of lines, aiming to match same lines:

.. literalinclude:: target.py
   :language: python
   :emphasize-lines: class Foo-pass, def bar(): pass-def block_start_with_comment, class Qux-

