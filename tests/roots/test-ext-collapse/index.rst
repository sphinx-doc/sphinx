Collapsible directive tests
===========================

.. collapse::

   Default section summary line

.. collapse:: Custom summary line for the collapsible content:

   Collapsible sections can also have custom summary lines

.. collapse:: Summary text here with **bold** and *em* and a :rfc:`2324`
                 reference! That was a newline in the reST source! We can also
                 have links_ and `more links <https://link2.example/>`__.

   This is some body text!

.. collapse:: Collapsible section with no content.
   :name: collapse-no-content
   :class: spam

.. collapse:: Collapsible section with reStructuredText content:

   Collapsible sections can have normal reST content such as **bold** and
   *emphasised* text, and also links_!

   .. _links: https://link.example/

.. collapse:: Collapsible section with titles:

   Collapsible sections can have sections:

   A Section
   ---------

   Some words within a section, as opposed to outwith the section.
