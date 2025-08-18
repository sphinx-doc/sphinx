test-toctree-only
=================

.. only:: not nonexistent

   hello world

   .. only:: text or not text

      .. js:data:: test_toctree_only1

      lorem ipsum dolor sit amet...

      .. only:: not lorem

         .. only:: not ipsum

            .. js:data:: test_toctree_only2

            lorem ipsum dolor sit amet...

         after ``only:: not ipsum``

   .. js:data:: test_toctree_only2

we're just normal men; we're just innocent men
