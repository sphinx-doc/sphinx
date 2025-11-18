Type Alias Cross-Reference Test
===============================

This tests that type aliases in function signatures can be cross-referenced properly.


.. py:module:: alias_module

   Module to test type alias cross-reference resolution.


.. py:data:: Handler
   :module: alias_module

   A generic type alias for error handlers

   alias of :py:class:`type`\ [:py:class:`Exception`]


.. py:type:: HandlerType
   :module: alias_module
   :canonical: type[Exception]

   A PEP 695 type alias for error handlers


.. py:data:: pathlike
   :module: alias_module
   :value: str | pathlib.Path

   Any type of path


.. py:function:: process_error(handler: Handler, other: ~alias_module.HandlerType) -> str
   :module: alias_module

   Process an error with a custom handler type.

   Tests generic type alias cross-reference resolution.


.. py:function:: read_file(path: pathlike) -> bytes
   :module: alias_module

   Read a file and return its contents.

   Tests Union type alias cross-reference resolution.
