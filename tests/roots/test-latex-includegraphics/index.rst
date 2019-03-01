====================
Test image inclusion
====================

Tests with both width and height
--------------------------------

.. an image with big dimensions, ratio H/W = 1/5
.. image:: img.png
   :height: 200
   :width: 1000

.. topic:: Oversized images

   .. an image with big dimensions, ratio H/W = 5/1
   .. image:: img.png
      :height: 1000
      :width: 200

   .. height too big even if width reduced to linewidth, ratio H/W = 3/1
   .. image:: img.png
      :width: 1000
      :height: 3000

Tests with only width or height
-------------------------------

.. topic:: Oversized images

   .. tall image which does not fit in textheight even if width rescaled
   .. image:: tall.png
      :width: 1000

.. wide image which does not fit in linewidth even after height diminished
.. image:: sphinx.png
   :height: 1000

