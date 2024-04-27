.. _collapsible:

:mod:`sphinx.ext.collapse` -- HTML collapsible content
======================================================

.. module:: sphinx.ext.collapse
   :synopsis: Support for collapsible content in HTML output.

.. versionadded:: 7.4

.. index:: single: collapse
           single: collapsible
           single: details
           single: summary
           pair: collapse; directive
           pair: details; directive
           pair: summary; directive

This extension provides a :rst:dir:`collapse` directive to provide support for
`collapsible content`_ in HTML output.

.. _collapsible content: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details

This extension is quite simple, and features only one directive:

.. rst:directive:: .. collapse:: <summary description>

   For HTML builders, this directive places the content of the directive
   into an HTML `details disclosure`_ element,
   with the *summary description* text included as the summary for the element.
   The *summary description* text is parsed as reStructuredText,
   and can be broken over multiple lines if required.

   Only the HTML 5 output format supports collapsible content.
   For other builders, the *summary description* text
   and the body of the directive are rendered in the document.

   .. _details disclosure: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details

   An example and the equivalent output are shown below:

   .. code-block:: reStructuredText

      .. collapse:: ``literal`` and **bold** content,
                    split over multiple lines.
         :open:

         This is the body of the directive.

         It is open by default as the ``:open:`` option was used.

         Markup Demonstration
         --------------------

         The body can also contain *markup*, including sections.

   .. collapse:: ``literal`` and **bold** content,
                 split over multiple lines.
      :open:

      This is the body of the directive.

      It is open by default as the ``:open:`` option was used.

      Markup Demonstration
      --------------------

      The body can also contain *markup*, including sections.

   .. versionadded:: 7.4

   .. rst:directive:option:: open

      Expand the collapsible content by default.

Internal node classes
---------------------

.. note:: These classes are only relevant to extension and theme developers.

.. autoclass:: collapsible
.. autoclass:: summary
