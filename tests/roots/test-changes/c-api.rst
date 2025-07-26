.. highlight:: c


Memory
======

.. c:function:: void* Test_Malloc(size_t n)

   Allocate *n* bytes of memory.

   .. version-changed:: 0.6

      Can now be replaced with a different allocator.

System
------

Access to the system allocator.

.. version-added:: 0.6

.. c:function:: void* Test_SysMalloc(size_t n)

   Allocate *n* bytes of memory using system allocator.
