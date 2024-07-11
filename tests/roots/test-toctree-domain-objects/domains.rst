test-domain-objects
===================

.. py:module:: hello

.. py:function:: world() -> str

   Prints "Hello, World!" to stdout

.. py:class:: HelloWorldPrinter

   Controls printing of hello world

   .. py:method:: set_language()

      Sets the language of the HelloWorldPrinter instance

   .. py:attribute:: output_count

      Count of outputs of "Hello, World!"

   .. py:method:: print_normal()
      :async:
      :classmethod:

      Prints the normal form of "Hello, World!"

   .. py:method:: print()

      Prints "Hello, World!", including in the chosen language

.. py:function:: exit()
   :module: sys

   Quits the interpreter

.. js:function:: fetch(resource)

   Fetches the given resource, returns a Promise